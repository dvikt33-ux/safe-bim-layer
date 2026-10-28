% МОАГ R12. Symbolic vertical enclosures, not measured 3D geometry.
% Data keeps all R11 source-qualified ordinal height and author-plan constraints.
int: n;
int: c;
int: q;
set of int: N=1..n;
set of int: C=1..c;
set of int: Q=1..q;
array[N] of set of int: level_domain;
array[N] of var 1..3: block;
array[N] of var 0..n: z;
array[N] of var 0..n: plan_x;
array[N] of var 0..n: plan_y;
array[N] of var 0..2*n: top;
array[C] of int: kind;
array[C] of N: a;
array[C] of N: b;
array[C] of bool: active;
array[Q] of N: parent;
array[Q] of N: upper;
constraint forall(i in N)(block[i] in level_domain[i]);
constraint forall(k in C)(active[k] ->
  if kind[k] = 1 then z[a[k]] > z[b[k]]
  elseif kind[k] = 2 then plan_x[a[k]] > plan_x[b[k]]
  else plan_y[a[k]] > plan_y[b[k]] endif);
% Parent floor < upper-floor < symbolic parent top. This is a *partial* local
% envelope relation only: no measured ceiling, full floor, or XY overlap.
constraint forall(k in Q)(
  z[parent[k]] < z[upper[k]] /\ z[upper[k]] < top[parent[k]]);
solve satisfy;
output ["{\"block\":" ++ show(block) ++ ",\"z\":" ++ show(z) ++
        ",\"plan_x\":" ++ show(plan_x) ++ ",\"plan_y\":" ++ show(plan_y) ++
        ",\"top\":" ++ show(top) ++ "}"];
