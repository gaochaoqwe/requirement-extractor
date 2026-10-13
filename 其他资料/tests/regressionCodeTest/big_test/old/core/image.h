#ifndef IMAGE_H
#define IMAGE_H

#include <string>
#include <vector>

struct Pixel {
    unsigned char r, g, b, a;
    
    Pixel() : r(0), g(0), b(0), a(255) {}
    Pixel(unsigned char red, unsigned char green, unsigned char blue, unsigned char alpha = 255)
        : r(red), g(green), b(blue), a(alpha) {}
};

class Image {
private:
    std::vector<std::vector<Pixel>> pixels;
    int width;
    int height;

public:
    Image();
    Image(int w, int h);
    ~Image();
    
    bool load(const std::string& filename);
    bool save(const std::string& filename);
    
    int getWidth() const;
    int getHeight() const;
    
    Pixel getPixel(int x, int y) const;
    void setPixel(int x, int y, const Pixel& pixel);
    
    void resize(int newWidth, int newHeight);
    void clear();
    
    // Basic operations
    void flipHorizontal();
    void flipVertical();
};

#endif // IMAGE_H 