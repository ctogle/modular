
// "2" can be number of captures, and need one argument per plot target
// "id" will correspond to the number in the ensemble batch

// a capture consists of inserting the next value into each results array

__kernel void simulate(__global float2* results)
{
    unsigned int id = get_global_id(0);

    results[id] = 1.0;
}

