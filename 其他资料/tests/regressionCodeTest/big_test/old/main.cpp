#include <iostream>
#include <string>
#include "core/image.h"
#include "filters/blur.h"
#include "utils/logger.h"

int main(int argc, char* argv[]) {
    Logger::init();
    Logger::info("Image Processor v1.0 started");
    
    if (argc < 2) {
        std::cerr << "Usage: " << argv[0] << " <image_file>" << std::endl;
        return 1;
    }
    
    std::string filename = argv[1];
    Logger::info("Loading image: " + filename);
    
    Image img;
    if (!img.load(filename)) {
        Logger::error("Failed to load image: " + filename);
        return 1;
    }
    
    // Apply blur filter
    BlurFilter blur;
    blur.apply(img);
    
    // Save processed image
    std::string output = "output_" + filename;
    img.save(output);
    
    Logger::info("Image processed and saved as: " + output);
    Logger::shutdown();
    
    return 0;
} 