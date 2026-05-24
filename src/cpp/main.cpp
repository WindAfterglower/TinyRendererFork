#include <cmath>
#include <cstdlib>
#include <iostream>
#include <string>
#include <utility>
#include "tgaimage.h"
#include "Util.h"

constexpr TGAColor white  = {255,255,255,255};
constexpr TGAColor green  = {0,255,0,255};
constexpr TGAColor red    = {0,0,255,255};
constexpr TGAColor blue   = {255,128,64,255};
constexpr TGAColor yellow = {0,200,255,255};

void line(int ax,int ay,int bx,int by,TGAImage &framebuffer,TGAColor color){
    bool steep = std::abs(ax - bx) < std::abs(ay-by);
    
    if(steep){
        std::swap(ax,ay);
        std::swap(by,bx);
    }
    
    if(ax > bx){
        std::swap(ax,bx);
        std::swap(ay,by);
    }
    int y = ay;
    int ierror = 0;
    for(float x = ax;x<=bx;x++){
        float t = (x - ax)/static_cast<float>(bx-ax);
        int y = std::round(ay + (by-ay)*t);
        
        if(steep)
            framebuffer.set(y,x,color);
        else
            framebuffer.set(x,y,color);
        ierror += 2 * std::abs(by-ay);
        //优雅但效率较低的写法，比最优解慢1秒多
        if(ierror > bx - ax){
            y+= by > ay?1:-1;
            ierror -= 2* (bx - ax);
        }
        //“丑陋”但效率较高的最优解写法
       // y+= by > ay?1:-1 * (ierror > bx -ax);
        //ierror -= 2* (bx - ax) * (ierror > bx -ax);


    }
}

int main(int argc,char** argv){
    constexpr int width  = 64;
    constexpr int height = 64;
    TGAImage framebuffer(width,height,TGAImage::RGB);
    
    int ax = 7,ay = 3;
    int bx = 12,by = 37;
    int cx = 62,cy = 53;

    
 std::srand(time({}));
    for (int i=0; i<(1<<24); i++) {
        int ax = rand()%width, ay = rand()%height;
        int bx = rand()%width, by = rand()%height;
        line(ax, ay, bx, by, framebuffer, { static_cast<uint8_t>(rand()%255), 
            static_cast<uint8_t>(rand()%255), 
            static_cast<uint8_t>(rand()%255),
             static_cast<uint8_t>(rand()%255) });
    }


/*
    line(ax,ay,bx,by,framebuffer,blue);
    line(bx,by,cx,cy,framebuffer,red);
    line(ax,ay,cx,cy,framebuffer,green);
    //line(cx,cy,ax,ay,framebuffer,yellow);

    framebuffer.set(ax,ay,red);
    framebuffer.set(bx,by,green);
    framebuffer.set(cx,cy,blue);*/

    framebuffer.write_tga_file("../TGA/framebuffer.tga");

   // PreviewTGA("python  ../TGA/tga_preview.py");

    std::cout<<"Writen End!";
    
    return 0;
}