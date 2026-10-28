% Symbolic witnesses only: ranks are neither metres nor complete floor decks.
int: n;
int: c;
set of int: N = 1..n;
set of int: C = 1..c;
array[N] of set of int: level_domain;
array[N] of var 1..3: block;
array[N] of var 0..n: z;
array[N] of var 0..n: plan_x;
array[N] of var 0..n: plan_y;
% kind 1: local elevation; 2/3: ordinal position on supplied plan.
array[C] of int: kind;
array[C] of N: a;
array[C] of N: b;
array[C] of bool: active;
constraint forall(i in N)(block[i] in level_domain[i]);
constraint forall(k in C)(active[k] ->
  if kind[k] = 1 then z[a[k]] > z[b[k]]
  elseif kind[k] = 2 then plan_x[a[k]] > plan_x[b[k]]
  else plan_y[a[k]] > plan_y[b[k]] endif);
solve satisfy;
output ["{\"block\":" ++ show(block) ++ ",\"z\":" ++ show(z) ++
        ",\"plan_x\":" ++ show(plan_x) ++ ",\"plan_y\":" ++ show(plan_y) ++ "}"];
