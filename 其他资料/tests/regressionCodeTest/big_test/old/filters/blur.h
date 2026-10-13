#ifndef BLUR_H
#define BLUR_H

#include "../core/image.h"

class BlurFilter {
private:
    int radius;
    
public:
    BlurFilter();
    BlurFilter(int r);
    
    void setRadius(int r);
    int getRadius() const;
    
    void apply(Image& image);
    
private:
    void gaussianBlur(Image& image);
    double gaussianWeight(int x, int y, double sigma);
};

#endif // BLUR_H 