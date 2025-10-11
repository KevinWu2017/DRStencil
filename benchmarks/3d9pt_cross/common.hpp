#ifndef __GEfloatRANDOM_HPP__
#define __GEfloatRANDOM_HPP__

#include <cmath>
#include <cstdlib>
#include <cstring>


float get_random() {
  return ((float)(rand())/(float)(RAND_MAX-1));
}


float* getRandom3DArray(int height, int width_y, int width_x) {
  float (*a)[width_y][width_x] =
    (float (*)[width_y][width_x])new float[height*width_y*width_x];
  for (int i = 0; i < height; i++)
    for (int j = 0; j < width_y; j++)
      for (int k = 0; k < width_x; k++) {
        a[i][j][k] = get_random();
      }
  return (float*)a;
}

float* getZero3DArray(int height, int width_y, int width_x) {
  float (*a)[width_y][width_x] =
    (float (*)[width_y][width_x])new float[height*width_y*width_x];
  memset((void*)a, 0, sizeof(float) * height * width_y * width_x);
  return (float*)a;
}

float checkError3D
(int width_y, int width_x, const float *l_output, const float *l_reference, int z_lb,
 int z_ub, int y_lb, int y_ub, int x_lb, int x_ub) {
  const float (*output)[width_y][width_x] =
    (const float (*)[width_y][width_x])(l_output);
  const float (*reference)[width_y][width_x] =
    (const float (*)[width_y][width_x])(l_reference);
  float error = 0.0;
  float max_error = 1e-13;
  int max_k = 0, max_j = 0, max_i = 0;
  for (int i = z_lb; i < z_ub; i++)
    for (int j = y_lb; j < y_ub; j++)
      for (int k = x_lb; k < x_ub; k++) {
	//printf ("real var1[%d][%d][%d] = %.6f and %.6f\n", i, j, k, reference[i][j][k], output[i][j][k]);
        float curr_error = output[i][j][k] - reference[i][j][k];
        curr_error = (curr_error < 0.0 ? -curr_error : curr_error);
        error += curr_error * curr_error;
        if (curr_error > max_error) {
          printf ("Values at index (%d,%d,%d) differ : %.6f and %.6f\n", i, j, k, reference[i][j][k], output[i][j][k]);
          max_error = curr_error;
          max_k = k;
          max_j = j;
          max_i = i;
        }
      }
  printf ("[Test] Max Error : %e @ (%d,%d,%d)\n", max_error, max_i, max_j, max_k);
  error = sqrt(error / ( (z_ub - z_lb) * (y_ub - y_lb) * (x_ub - x_lb)));
  return error;
}

#endif
