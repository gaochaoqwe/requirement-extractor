#ifndef SHARPEN_H
#define SHARPEN_H

#include "../core/image.h"

class SharpenFilter {
private:
    double strength;
    
public:
    SharpenFilter();
    SharpenFilter(double s);
    
    void setStrength(double s);
    double getStrength() const;
    
    void apply(Image& image);
    
private:
    void unsharpMask(Image& image);
    void laplacianSharpen(Image& image);
};

#endif // SHARPEN_H 