
//__kernel void simulate(__global float* results)
//{
//    unsigned int id = get_global_id(0);
//}

__kernel void part1(__global float* a, __global float* b, __global float* c)
{
    unsigned int i = get_global_id(0);
    c[i] = a[i] + b[i];
}
