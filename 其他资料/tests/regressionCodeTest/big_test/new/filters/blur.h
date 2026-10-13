#ifndef BLUR_H
#define BLUR_H

#include "../core/image.h"

enum BlurType {
    BLUR_GAUSSIAN = 0,
    BLUR_BOX = 1,
    BLUR_MOTION = 2  // New blur type
};

class BlurFilter {
private:
    int radius;
    BlurType type;  // New field
    double angle;   // New field for motion blur
    
public:
    BlurFilter();
    BlurFilter(int r);
    BlurFilter(int r, BlurType t);  // New constructor
    BlurFilter(int r, BlurType t, double a);  // New constructor for motion blur
    
    void setRadius(int r);
    int getRadius() const;
    
    void setType(BlurType t);  // New method
    BlurType getType() const;  // New method
    
    void setAngle(double a);   // New method
    double getAngle() const;   // New method
    
    void apply(Image& image);
    
private:
    void gaussianBlur(Image& image);
    void boxBlur(Image& image);        // New method
    void motionBlur(Image& image);     // New method
    double gaussianWeight(int x, int y, double sigma);
};

#endif // BLUR_H 