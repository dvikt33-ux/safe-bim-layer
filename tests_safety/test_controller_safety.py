"""Headless tests of real controller methods; no live GUI or BIM."""
import threading
import unittest
from unittest.mock import Mock
from controller.app import ControllerApp
from controller.client import RuntimeState


class Value:
    def __init__(self):self.value=None
    def set(self,value):self.value=value


class Combo(dict):
    def get(self):return self.selected


class ControllerSafetyTests(unittest.TestCase):
    def app(self):
        a=ControllerApp.__new__(ControllerApp)
        a.job_id='active';a.alive=True;a.log=Mock();a.selection_generation=0
        a._request_serial=a._rendered_serial=0;a._poll_lock=threading.Lock()
        a._displayed_state=None;a._history_targets={}
        a.vars={k:Value() for k in ('status','enum','job','step','progress','floor','readback','message')}
        a.history=Combo();a.continue_button=Mock();a.pause_button=Mock();a.stop_button=Mock()
        a.root=Mock();a.root.after.side_effect=lambda delay,fn:fn() if delay==0 else None
        a.client=Mock()
        return a
    def state(self,job='A',revision=0,status='PAUSED',history=()):
        return RuntimeState(job,job,status,'step','1/1',1,'verified',status,
                            history=history,controls={'continue':True,'pause':True,'stop':True},
                            revision=revision,capability='epoch-capability')

    def test_history_A_display_commands_A_not_current_B(self):
        a=self.app();a.job_id='A';a.show_state(self.state('A'))
        done=threading.Event();targets=[]
        def command(action,job,**kw):targets.append((action,job,kw));done.set()
        a.client.command.side_effect=command
        a.command('continue');self.assertTrue(done.wait(3))
        self.assertEqual(targets,[('continue','A',{'revision':0,'capability':'epoch-capability'})])

    def test_late_active_poll_cannot_overwrite_history_selection(self):
        a=self.app();entered=threading.Event();release=threading.Event()
        def state(job):
            if job=='active':entered.set();release.wait(4);return self.state('B')
            return self.state('A')
        a.client.state.side_effect=state
        thread=threading.Thread(target=a._read_state);thread.start();self.assertTrue(entered.wait(3))
        a.job_id='A';a.selection_generation+=1;a._read_state()
        release.set();thread.join(4)
        self.assertEqual(a._displayed_state.job_id,'A')
        self.assertEqual(a.vars['job'].value,'A / A')

    def test_older_revision_poll_cannot_replace_fresh_display(self):
        a=self.app();a.show_state(self.state('A',revision=7))
        a.client.state.return_value=self.state('A',revision=2)
        a._read_state();self.assertEqual(a._displayed_state.revision,7)

    def test_malformed_history_disables_controls_before_error(self):
        a=self.app();a.show_state(self.state());a.continue_button.reset_mock()
        with self.assertRaises(ValueError):a.show_state(self.state(status='DONE',history=({},)))
        a.continue_button.configure.assert_called_once_with(state='disabled')
        self.assertIsNone(a._displayed_state)

    def test_disconnect_and_terminal_states_cannot_send_commands(self):
        a=self.app();a.show_state(self.state());a.disconnected();a.command('continue')
        a.client.command.assert_not_called()
        for status in ('DONE','FAILED','CANCELLED'):
            a.show_state(self.state(status=status));a.command('continue');a.command('pause');a.command('stop')
            a.client.command.assert_not_called()
            a.continue_button.configure.assert_called_with(state='disabled')

    def test_current_mode_option_is_always_available(self):
        a=self.app();a.job_id='old'
        a.show_state(self.state('old',history=({'job_id':'old','status':'DONE','task_name':'old'},)))
        self.assertEqual(a._history_targets['Текущая задача / Current'],'active')
        a.history.selected='Текущая задача / Current';a._read_state=Mock()
        a.select_history();self.assertEqual(a.job_id,'active');self.assertIsNone(a._displayed_state)

    def test_state_for_wrong_concrete_job_fails_closed(self):
        a=self.app();a.job_id='A';a.client.state.return_value=self.state('B');a._read_state()
        self.assertIsNone(a._displayed_state);self.assertEqual(a.vars['enum'].value,'DISCONNECTED')

    def test_display_epoch_capability_not_new_background_client_epoch(self):
        a=self.app();a.show_state(self.state('A'));done=threading.Event();sent=[]
        a.client.command.side_effect=lambda *args,**kw:(sent.append(kw),done.set())
        a.client._states={'A':self.state('A',revision=10)}
        a.command('continue');self.assertTrue(done.wait(3))
        self.assertEqual(sent[0]['capability'],'epoch-capability')
        self.assertEqual(sent[0]['revision'],0)

if __name__=='__main__':unittest.main()
