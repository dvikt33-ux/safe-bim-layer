% R15 linear/disjunctive adapter to the ready CP-SAT backend.
% Every numerical value is a scenario witness, never metres/book geometry.
int: nv; int: ng; int: nr; int: nt;
set of int: V=1..nv; set of int: G=1..ng; set of int: R=1..nr;
array[V] of set of int: domains;
array[V] of var int: value;
array[G] of bool: active;
array[G] of bool: disjunction;
array[R] of G: group;
array[R] of int: rhs;
array[R] of 0..nv: condition_var;
array[R] of int: condition_value;
array[1..nt] of V: term_var;
array[1..nt] of int: term_coefficient;
array[1..nt] of R: term_row;
constraint forall(i in V)(value[i] in domains[i]);
array[R] of var bool: satisfied = [
  (if condition_var[r]=0 then true else value[condition_var[r]]=condition_value[r] endif)
  -> sum(k in 1..nt where term_row[k]=r)(term_coefficient[k]*value[term_var[k]])>=rhs[r]
  | r in R];
constraint forall(g in G)(active[g] ->
  if disjunction[g] then exists(r in R where group[r]=g)(satisfied[r])
  else forall(r in R where group[r]=g)(satisfied[r]) endif);
solve satisfy;
output ["{\"values\":"++show(value)++"}"];
