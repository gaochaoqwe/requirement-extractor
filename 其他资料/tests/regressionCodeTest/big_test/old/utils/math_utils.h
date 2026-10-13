#ifndef MATH_UTILS_H
#define MATH_UTILS_H

#ifdef __cplusplus
extern "C" {
#endif

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

// Clamp functions
double clamp(double value, double min, double max);
int clamp_int(int value, int min, int max);

// Interpolation
double lerp(double a, double b, double t);

// Geometry
double distance(double x1, double y1, double x2, double y2);
double normalize_angle(double angle);

// Mathematical functions
int factorial(int n);
double power(double base, int exponent);

#ifdef __cplusplus
}
#endif

#endif // MATH_UTILS_H 