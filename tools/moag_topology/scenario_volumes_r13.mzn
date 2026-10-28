% МОАГ R13: artificial 3D bounding-box consistency, NOT authored station geometry.
% All grid dimensions are candidate scenario units, NEVER metres or book measures.
int: n; int: ne; int: nh;
set of int: N=1..n; set of int: E=1..ne; set of int: H=1..nh;
array[N] of int: dw; array[N] of int: dd; array[N] of int: dh;
array[N] of int: bw; array[N] of int: bd; array[N] of int: bh;
array[N] of 0..n: parent;
array[E] of N: e1; array[E] of N: e2;
array[H] of N: h1; array[H] of N: h2;
array[H] of 1..2: haxis;
array[N] of var 0..100: x;
array[N] of var 0..100: y;
array[N] of var 0..100: z;
constraint forall(i in N)(
  x[i]+dw[i]<=bw[i] /\ y[i]+dd[i]<=bd[i] /\ z[i]+dh[i]<=bh[i]);
constraint forall(i in N where parent[i]>0)(
  x[i]>=x[parent[i]] /\ y[i]>=y[parent[i]] /\ z[i]>z[parent[i]] /\
  x[i]+dw[i]<=x[parent[i]]+dw[parent[i]] /\
  y[i]+dd[i]<=y[parent[i]]+dd[parent[i]] /\
  z[i]+dh[i]<=z[parent[i]]+dh[parent[i]]);
% Only source-disambiguated separately identified physical spaces.
% Other pairs remain UNKNOWN: do not invent a non-overlap constraint.
constraint forall(k in E)(
   x[e1[k]]+dw[e1[k]]<=x[e2[k]] \/
   x[e2[k]]+dw[e2[k]]<=x[e1[k]] \/
   y[e1[k]]+dd[e1[k]]<=y[e2[k]] \/
   y[e2[k]]+dd[e2[k]]<=y[e1[k]] \/
   z[e1[k]]+dh[e1[k]]<=z[e2[k]] \/
   z[e2[k]]+dh[e2[k]]<=z[e1[k]]);
% These are on-page label-order hints, not absolute cardinal directions.
constraint forall(k in H)(
  if haxis[k]=1 then 2*x[h1[k]]+dw[h1[k]]>2*x[h2[k]]+dw[h2[k]]
  else 2*y[h1[k]]+dd[h1[k]]>2*y[h2[k]]+dd[h2[k]] endif);
solve satisfy;
output ["{\"x\":"++show(x)++",\"y\":"++show(y)++",\"z\":"++show(z)++"}"];
