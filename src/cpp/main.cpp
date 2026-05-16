#include <cmath>
#include <iostream>
#include "tgaimage.h"

constexpr TGAColor white  = {255,255,255,255};
constexpr TGAColor green  = {0,255,0,255};
constexpr TGAColor red    = {0,0,255,255};
constexpr TGAColor blue   = {255,128,64,255};
constexpr TGAColor yellow = {0,200,255,255};

void line(int ax,int ay,int bx,int by,TGAImage &framebuffer,TGAColor color){
    for(float t = 0;t<1;t+=.02){
        int x = std::round(ax + (bx-ax)*t);
        int y = std::round(ay + (by-ay)*t);
        framebuffer.set(x,y,color);
    }
}

int main(int argc,char** argv){
    constexpr int width  = 64;
    constexpr int height = 64;
    TGAImage framebuffer(width,height,TGAImage::RGB);
    
    int ax = 7,ay = 3;
    int bx = 12,by = 37;
    int cx = 62,cy = 53;


    line(ax,ay,bx,by,framebuffer,blue);
    line(bx,by,cx,cy,framebuffer,red);
    line(ax,ay,cx,cy,framebuffer,green);

    framebuffer.set(ax,ay,red);
    framebuffer.set(bx,by,green);
    framebuffer.set(cx,cy,blue);

    framebuffer.write_tga_file("../TGA/framebuffer.tga");
    std::cout<<"Writen End!";
    
    return 0;
}