#ifndef MATH_UTILS_H
#define MATH_UTILS_H

#ifdef __cplusplus
extern "C" {
#endif

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

// Enhanced clamp functions
double clamp(double value, double min, double max);
int clamp_int(int value, int min, int max);
float clamp_float(float value, float min, float max);  // New function

// Interpolation functions
double lerp(double a, double b, double t);
double smoothstep(double edge0, double edge1, double x);  // New function
double smootherstep(double edge0, double edge1, double x);  // New function

// Geometry functions
double distance(double x1, double y1, double x2, double y2);
double distance3d(double x1, double y1, double z1, double x2, double y2, double z2);  // New function
double normalize_angle(double angle);
double angle_between_vectors(double x1, double y1, double x2, double y2);  // New function

// Mathematical functions
int factorial(int n);
double power(double base, int exponent);
double fast_inverse_sqrt(double x);  // New function
double deg_to_rad(double degrees);   // New function
double rad_to_deg(double radians);   // New function

// Vector operations (new)
typedef struct {
    double x, y, z;
} Vector3;

Vector3 vector3_add(Vector3 a, Vector3 b);
Vector3 vector3_subtract(Vector3 a, Vector3 b);
Vector3 vector3_multiply(Vector3 v, double scalar);
double vector3_dot(Vector3 a, Vector3 b);
Vector3 vector3_cross(Vector3 a, Vector3 b);
double vector3_length(Vector3 v);
Vector3 vector3_normalize(Vector3 v);

#ifdef __cplusplus
}
#endif

#endif // MATH_UTILS_H 