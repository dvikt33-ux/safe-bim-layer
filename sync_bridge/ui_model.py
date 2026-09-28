"""Safe BIM shell state. No Tapir details in the normal view."""
from __future__ import annotations

from sync_bridge.connections import ConnectionBoard
from sync_bridge.context import UI_REFRESH, UI_STALE


class SafeBIMUI:
    def __init__(self):
        self.project = 'Test_House'
        self.story = 1
        self.selection = '6 стен'
        self.safe = True
        self.command_open = False
        self.ai_open = False
        self.code_open = False
        self.history_open = False
        self.check_open = False
        self.ai_route = 'online'
        self.error = ''
        self.show_technical = False
        self.connections = ConnectionBoard()
        self.context_banner = ''
        self.board = None

    def click(self, panel: str) -> None:
        if panel == 'command':
            self.command_open = not self.command_open
        elif panel == 'ai':
            self.ai_open = not self.ai_open
        elif panel == 'code':
            self.code_open = not self.code_open
        elif panel == 'history':
            self.history_open = not self.history_open
        elif panel == 'check':
            self.check_open = not self.check_open
        else:
            raise KeyError(panel)

    def on_ai_response(self, proposal) -> None:
        self.last_proposal = proposal

    def on_future_code_success(self) -> None:
        self.code_open = False

    def set_offline_ai(self) -> None:
        self.ai_route = 'offline'
        self.connections.mark_internet_offline()

    def set_local_ai(self) -> None:
        self.ai_route = 'local'

    def set_online(self) -> None:
        self.ai_route = 'online'
        self.connections.set('AI', 'CONNECTED', 'облако')
        self.connections.set('REMOTE', 'CONNECTED', 'mailbox')

    def show_error(self, text: str) -> None:
        self.error = text
        self.show_technical = False

    def render(self) -> str:
        ai = {'online': 'ИИ: ● Онлайн', 'offline': 'ИИ: ● Офлайн', 'local': 'ИИ: ● Локальная'}[self.ai_route]
        lines = [
            'SAFE BIM                    ● SAFE' if self.safe else 'SAFE BIM                    ● CHECK',
            f'Проект: {self.project}',
            f'Этаж: {self.story}',
            f'Выбрано: {self.selection}',
            ai,
            f"Bridge: {_dot(self.connections.get('BRIDGE')['status'])}",
            f"GitHub: {_dot(self.connections.get('REMOTE')['status'])}",
        ]
        if self.context_banner:
            lines.append(self.context_banner)
        if self.error:
            lines.append(self.error)
        if self.show_technical:
            lines.append('TECHNICAL')
        if self.board:
            lines.append(f"LOCAL {self.board['LOCAL']}")
            lines.append(f"REMOTE {self.board['REMOTE']}")
            lines.append(f"AI {self.board['AI']}")
            lines.append(f"ARCHICAD {self.board['ARCHICAD']}")
        return '\n'.join(lines)

    def apply_board(self, board: dict) -> None:
        self.board = dict(board)
        self.local_ready = board.get('LOCAL') == 'LOCAL_READY'
        self.needs_auth = board.get('REMOTE') == 'REMOTE_NEEDS_AUTH'

    def apply_context_lease(self, lease: str, banner: str) -> None:
        self.context_banner = banner
        if lease == 'STALE':
            self.context_banner = UI_STALE
        self.refresh_label = UI_REFRESH


def _dot(status: str) -> str:
    return {'CONNECTED': '●', 'CONNECTING': '○', 'DEGRADED': '◐', 'OFFLINE': '○', 'ERROR': '!'}.get(status, '?')
