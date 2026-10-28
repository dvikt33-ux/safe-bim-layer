% MOAG R14: keep all 52 observed route sequences and 32 explicitly recorded
% relative height relations. Variables are ordinal NONMETRIC witnesses.
int: n;
int: nz;
int: nt;
set of int: N=1..n;
set of int: Z=1..nz;
set of int: T=1..nt;
array[N] of int: lo;
array[N] of int: hi;
array[N] of var 0..5*n: z;
array[N] of var 0..n: t;
array[Z] of N: high;
array[Z] of N: low;
array[T] of N: earlier;
array[T] of N: later;
constraint forall(i in N)(z[i]>=lo[i] /\ z[i]<=hi[i]);
constraint forall(i in Z)(z[high[i]]>z[low[i]]);
% t denotes the documented *narrative sequence*, not minutes or route length.
% No direct physical door or straight corridor is inferred by the next line.
constraint forall(i in T)(t[later[i]]>t[earlier[i]]);
solve satisfy;
output ["{\"z\":"++show(z)++",\"t\":"++show(t)++"}"];
