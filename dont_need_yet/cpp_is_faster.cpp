#include <vector>
#include <string>
#include <chrono>
#include <fstream>

struct SimpleImage {
    int width, height;
    std::vector<std::vector<std::vector<uint8_t>>> pixels;
    
    SimpleImage(int w, int h) : width(w), height(h) {
        pixels.resize(h, std::vector<std::vector<uint8_t>>(w, std::vector<uint8_t>(3, 0)));
    }
    
    std::vector<uint8_t> getPixel(int x, int y) const {
        if (x >= 0 && x < width && y >= 0 && y < height) {
            return pixels[y][x];
        }
        return {0, 0, 0};
    }
    
    void putPixel(int x, int y, const std::vector<uint8_t>& color) {
        if (x >= 0 && x < width && y >= 0 && y < height) {
            pixels[y][x] = color;
        }
    }
    
    std::vector<uint8_t> toJpeg() const {
        std::string temp_ppm = "temp_output.ppm";
        std::ofstream file(temp_ppm, std::ios::binary);
        file << "P6\n" << width << " " << height << "\n255\n";
        
        for (int y = 0; y < height; y++) {
            for (int x = 0; x < width; x++) {
                auto pixel = getPixel(x, y);
                file << static_cast<char>(pixel[0]) 
                     << static_cast<char>(pixel[1]) 
                     << static_cast<char>(pixel[2]);
            }
        }
        file.close();
        
        system("convert temp_output.ppm temp_output.jpg 2>/dev/null");
        
        std::ifstream jpeg_file("temp_output.jpg", std::ios::binary);
        std::vector<uint8_t> jpeg_data((std::istreambuf_iterator<char>(jpeg_file)), 
                                      std::istreambuf_iterator<char>());
        jpeg_file.close();
        
        remove("temp_output.ppm");
        remove("temp_output.jpg");
        
        return jpeg_data;
    }
};

struct DeadZones {
    bool isBackpack;
    bool isEyes;
    bool isLegspace;
};

DeadZones check_dead_zones(int x, int y, int spawn_x, int spawn_y, int w, int h) {
    DeadZones result = {false, false, false};
    
    if (x <= (spawn_x + w/4) && (y <= (spawn_y + h/4) || y >= (spawn_y + 3*h/4))) {
        result.isBackpack = true;
    }
    
    if (x >= (spawn_x + w/2) && x <= (spawn_x + w) && 
        y >= (spawn_y + h/8) && y <= (spawn_y + 3*h/8)) {
        result.isEyes = true;
    }
    
    if (x >= (spawn_x + w/2) && x <= (spawn_x + 3*w/4) && 
        y >= (spawn_y + 7*h/8) && y <= (spawn_y + h)) {
        result.isLegspace = true;
    }
    
    return result;
}

bool convertToPPM(const std::string& input_path, const std::string& output_path) {
    std::string command = "convert \"" + input_path + "\" \"" + output_path + "\" 2>/dev/null";
    return system(command.c_str()) == 0;
}

SimpleImage loadPPM(const std::string& filename) {
    std::ifstream file(filename, std::ios::binary);
    if (!file) {
        return SimpleImage(1, 1);
    }
    
    std::string format;
    int width, height, maxval;
    file >> format >> width >> height >> maxval;
    
    if (format != "P6") {
        return SimpleImage(1, 1);
    }
    
    file.ignore(256, '\n');
    
    SimpleImage img(width, height);
    for (int y = 0; y < height; y++) {
        for (int x = 0; x < width; x++) {
            char r, g, b;
            file.read(&r, 1);
            file.read(&g, 1); 
            file.read(&b, 1);
            img.pixels[y][x] = {
                static_cast<uint8_t>(r), 
                static_cast<uint8_t>(g), 
                static_cast<uint8_t>(b)
            };
        }
    }
    
    return img;
}

void amogus_pattern(SimpleImage& img, int w, int h, int spawn_x, int spawn_y, int width, int height) {
    int end_x = spawn_x + w;
    int end_y = spawn_y + h;
    
    long red_total = 0, green_total = 0, blue_total = 0;
    int pixel_count = 0;
    
    for (int x = spawn_x; x < end_x; x++) {
        for (int y = spawn_y; y < end_y; y++) {
            if (x < width && y < height) {
                auto color = img.getPixel(x, y);
                red_total += color[0];
                green_total += color[1];
                blue_total += color[2];
                pixel_count++;
            }
        }
    }
    
    if (pixel_count == 0) return;
    
    int R_avg = red_total / pixel_count;
    int G_avg = green_total / pixel_count;
    int B_avg = blue_total / pixel_count;
    
    std::vector<uint8_t> color_avg = {static_cast<uint8_t>(R_avg), static_cast<uint8_t>(G_avg), static_cast<uint8_t>(B_avg)};
    std::vector<uint8_t> lighter_color_avg = {
        static_cast<uint8_t>(std::min(255, R_avg * 5/4)),
        static_cast<uint8_t>(std::min(255, G_avg * 5/4)), 
        static_cast<uint8_t>(std::min(255, B_avg * 5/4))
    };
    std::vector<uint8_t> darker_color_avg = {
        static_cast<uint8_t>(std::max(0, R_avg * 3/4)),
        static_cast<uint8_t>(std::max(0, G_avg * 3/4)),
        static_cast<uint8_t>(std::max(0, B_avg * 3/4))
    };
    
    for (int x = spawn_x; x < end_x; x++) {
        for (int y = spawn_y; y < end_y; y++) {
            if (x < width && y < height) {
                DeadZones zones = check_dead_zones(x, y, spawn_x, spawn_y, w, h);
                
                if (!zones.isBackpack && !zones.isEyes && !zones.isLegspace) {
                    img.putPixel(x, y, color_avg);
                } else if (!zones.isBackpack && !zones.isLegspace && zones.isEyes) {
                    img.putPixel(x, y, lighter_color_avg);
                } else if (!zones.isEyes && (zones.isBackpack || zones.isLegspace)) {
                    img.putPixel(x, y, darker_color_avg);
                }
            }
        }
    }
}

extern "C" {
    const uint8_t* blur_image(const char* image_path, int chunk_size, int* data_size) {
        static std::vector<uint8_t> result;
        
        std::string ppm_path = "temp_input.ppm";
        if (!convertToPPM(image_path, ppm_path)) {
            return nullptr;
        }
        
        SimpleImage img = loadPPM(ppm_path);
        remove(ppm_path.c_str());
        
        int width = img.width;
        int height = img.height;
        
        for (int x = 0; x <= width; x += chunk_size) {
            for (int y = 0; y <= height; y += chunk_size) {
                amogus_pattern(img, chunk_size, chunk_size, x, y, width, height);
            }
        }
        
        result = img.toJpeg();
        *data_size = result.size();
        return result.data();
    }
}