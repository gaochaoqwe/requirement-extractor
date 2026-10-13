#include "math_utils.h"
#include <math.h>

// Enhanced clamp functions
double clamp(double value, double min, double max) {
    if (value < min) return min;
    if (value > max) return max;
    return value;
}

int clamp_int(int value, int min, int max) {
    if (value < min) return min;
    if (value > max) return max;
    return value;
}

float clamp_float(float value, float min, float max) {
    if (value < min) return min;
    if (value > max) return max;
    return value;
}

// Interpolation functions
double lerp(double a, double b, double t) {
    return a + t * (b - a);
}

double smoothstep(double edge0, double edge1, double x) {
    double t = clamp((x - edge0) / (edge1 - edge0), 0.0, 1.0);
    return t * t * (3.0 - 2.0 * t);
}

double smootherstep(double edge0, double edge1, double x) {
    double t = clamp((x - edge0) / (edge1 - edge0), 0.0, 1.0);
    return t * t * t * (t * (t * 6.0 - 15.0) + 10.0);
}

// Geometry functions
double distance(double x1, double y1, double x2, double y2) {
    double dx = x2 - x1;
    double dy = y2 - y1;
    return sqrt(dx * dx + dy * dy);
}

double distance3d(double x1, double y1, double z1, double x2, double y2, double z2) {
    double dx = x2 - x1;
    double dy = y2 - y1;
    double dz = z2 - z1;
    return sqrt(dx * dx + dy * dy + dz * dz);
}

double normalize_angle(double angle) {
    while (angle > M_PI) angle -= 2.0 * M_PI;
    while (angle < -M_PI) angle += 2.0 * M_PI;
    return angle;
}

double angle_between_vectors(double x1, double y1, double x2, double y2) {
    double dot = x1 * x2 + y1 * y2;
    double len1 = sqrt(x1 * x1 + y1 * y1);
    double len2 = sqrt(x2 * x2 + y2 * y2);
    
    if (len1 == 0.0 || len2 == 0.0) return 0.0;
    
    return acos(clamp(dot / (len1 * len2), -1.0, 1.0));
}

// Mathematical functions
int factorial(int n) {
    if (n <= 1) return 1;
    
    // Enhanced with iterative approach for better performance
    int result = 1;
    for (int i = 2; i <= n; i++) {
        result *= i;
    }
    return result;
}

double power(double base, int exponent) {
    if (exponent == 0) return 1.0;
    if (exponent < 0) return 1.0 / power(base, -exponent);
    
    // Enhanced with fast exponentiation
    double result = 1.0;
    double current_power = base;
    
    while (exponent > 0) {
        if (exponent & 1) {
            result *= current_power;
        }
        current_power *= current_power;
        exponent >>= 1;
    }
    
    return result;
}

double fast_inverse_sqrt(double x) {
    // Fast inverse square root approximation
    if (x <= 0.0) return 0.0;
    
    double half = 0.5 * x;
    long long i = *(long long*)&x;
    i = 0x5FE6EB50C7B537A9 - (i >> 1);
    x = *(double*)&i;
    x = x * (1.5 - half * x * x);
    x = x * (1.5 - half * x * x);  // Second iteration for better precision
    
    return x;
}

double deg_to_rad(double degrees) {
    return degrees * M_PI / 180.0;
}

double rad_to_deg(double radians) {
    return radians * 180.0 / M_PI;
}

// Vector operations
Vector3 vector3_add(Vector3 a, Vector3 b) {
    Vector3 result;
    result.x = a.x + b.x;
    result.y = a.y + b.y;
    result.z = a.z + b.z;
    return result;
}

Vector3 vector3_subtract(Vector3 a, Vector3 b) {
    Vector3 result;
    result.x = a.x - b.x;
    result.y = a.y - b.y;
    result.z = a.z - b.z;
    return result;
}

Vector3 vector3_multiply(Vector3 v, double scalar) {
    Vector3 result;
    result.x = v.x * scalar;
    result.y = v.y * scalar;
    result.z = v.z * scalar;
    return result;
}

double vector3_dot(Vector3 a, Vector3 b) {
    return a.x * b.x + a.y * b.y + a.z * b.z;
}

Vector3 vector3_cross(Vector3 a, Vector3 b) {
    Vector3 result;
    result.x = a.y * b.z - a.z * b.y;
    result.y = a.z * b.x - a.x * b.z;
    result.z = a.x * b.y - a.y * b.x;
    return result;
}

double vector3_length(Vector3 v) {
    return sqrt(v.x * v.x + v.y * v.y + v.z * v.z);
}

Vector3 vector3_normalize(Vector3 v) {
    double len = vector3_length(v);
    if (len > 0.0) {
        return vector3_multiply(v, 1.0 / len);
    }
    
    Vector3 zero = {0.0, 0.0, 0.0};
    return zero;
} 