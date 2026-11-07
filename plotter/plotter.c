#include <stdio.h>
#include <stdlib.h>
#include <stdbool.h>
#include <time.h>
#include <raylib.h>

#define WIDTH 1120
#define HEIGHT 840
#define PLOT_MARGIN 50
#define POINT_SIZE 5

#define MAX_SAMPLES 200
#define MEASURE_COUNT 10
#define PIXELS_PER_MEASURE (WIDTH / MEASURE_COUNT)

#define PYTHON_MODULE_PATH "../preprocessor/preprocessor.py"
#define OUTPUT_FILE        "./total_results.txt"

typedef struct {
    float t, rpm;
} Sample;

typedef struct {
    float t, rpm;
    float x, y;
    bool isGap;
} Point;

// TODO: Allocate memory for samples dynamically
Sample samples[MAX_SAMPLES] = {0};
Point points[MAX_SAMPLES] = {0};
// TODO: Maybe organize these metadata into a struct?
int lowerY, upperY;
int timeSpan;
int sampleCount;
int pointCount;

// Convert from [lowerY..upperY] to [PLOT_MARGIN..HEIGHT-PLOT_MARGIN]
float ScreenY(float y)
{
    // [lowerY..upperY]   - lowerY
    // [0..upperY-lowerY] / upperY-lowerY
    // [0..1] * HEIGHT
    return (1 - ((y - lowerY) / (upperY-lowerY))) * (HEIGHT - 2*PLOT_MARGIN) + PLOT_MARGIN;
}

// Convert from [0..timeSpan] to [PLOT_MARGIN..WIDTH-PLOT_MARGIN]
float ScreenX(float x)
{
    // [0..timeSpan] / timeSpan
    // [0..1] * WIDTH
    return (x / timeSpan) * (WIDTH - 2*PLOT_MARGIN) + PLOT_MARGIN;
}

void RenderAxis(void)
{
    // Vertical
    DrawLine(PLOT_MARGIN, HEIGHT-PLOT_MARGIN, PLOT_MARGIN, PLOT_MARGIN, WHITE);    
    // Horizontal
    DrawLine(PLOT_MARGIN, HEIGHT-PLOT_MARGIN, WIDTH-PLOT_MARGIN, HEIGHT-PLOT_MARGIN, WHITE);    
}

void SetPointsScreenCoords(void)
{
    for (int i = 0; i < pointCount; i++) {
        Point *point = &points[i];
        point->x = ScreenX(point->t);
        point->y = ScreenY(point->rpm);
    }
}

void RenderPlot(void)
{
    SetPointsScreenCoords();
    Point firstPoint;
    for (int i = 0; i < pointCount; i++) {
        if (i == 0) {
            firstPoint = points[0];
            DrawCircle(firstPoint.x, firstPoint.y, POINT_SIZE, RED);
            continue;
        }
        Point secondPoint = points[i];
        Color lineColor = firstPoint.isGap ? GRAY : RED;
        DrawLine(firstPoint.x, firstPoint.y, secondPoint.x, secondPoint.y, lineColor);
        DrawCircle(secondPoint.x, secondPoint.y, POINT_SIZE, RED);
        firstPoint = secondPoint;
    }
}

int LoadSamples(const char *input_file)
{
    Sample sample_buf = {0};
    int samplei = 0;
    int c;
    FILE *f = fopen(input_file, "r");
    if (!f) {
        fprintf(stderr, "ERROR: could not open file %s\n", input_file);
        exit(1);
    }
    
    if (fscanf(f, "%d", &sampleCount) != 1)
        return -1;
    if (fscanf(f, "%d", &timeSpan) != 1)
        return -1;
    if (fscanf(f, "%d%d", &lowerY, &upperY) != 2)
        return -1;

    while (fscanf(f, "%f%f", &(sample_buf.t), &(sample_buf.rpm)) == 2)
        samples[samplei++] = sample_buf;
    return 0;
}

void CallPythonModule(const char *input_file)
{
    char python_call_cmd[128];
    snprintf(python_call_cmd, 128,
             "python %s %s raw %s", PYTHON_MODULE_PATH, input_file, OUTPUT_FILE);
    system(python_call_cmd); // TODO: Check for errors
}

void CompressSamples(void)
{
    float batchSize = (float) timeSpan / MEASURE_COUNT;
    float accumulatedInterval = 0.0f;
    float accumulatedRpm = 0.0f;

    for (int samplei = 0; samplei < sampleCount; samplei++) {
        Sample current = samples[samplei];
        if (samplei == 0) {
            points[pointCount++] = (Point) {
                .t = samples[0].t,
                .rpm = samples[0].rpm,
                .isGap = false
            };
            continue;
        } else if (samplei == sampleCount - 1) {
            points[pointCount++] = (Point) {
                .t = samples[samplei].t,
                .rpm = accumulatedRpm / accumulatedInterval,
                .isGap = false
            };
            break;
        }
        Sample next = samples[samplei + 1];
        float interval = next.t - current.t;
        if (interval > 1.5f) {
            points[pointCount++] = (Point) {
                .t = current.t,
                .rpm = accumulatedRpm / accumulatedInterval,
                .isGap = true
            };
            points[pointCount++] = (Point) {
                .t = next.t,
                .rpm = next.rpm,
                .isGap = false
            };
            accumulatedInterval = next.rpm - batchSize*((int) (next.rpm / batchSize));
            accumulatedRpm = 0.0f;
            continue;
        }
        if (batchSize - accumulatedInterval <= 0) {
            points[pointCount++] = (Point) {
                .t = current.t,
                .rpm = accumulatedRpm / accumulatedInterval,
                .isGap = false
            };
            accumulatedInterval = accumulatedRpm = 0.0f;
        }
        accumulatedInterval += interval;
        accumulatedRpm += current.rpm;
    }
}

void ShowPointDetails(Point *point)
{
    char pointInfoBuf[128];
    snprintf(pointInfoBuf, 128, "t: %.2f\nrpm: %.2f", point->t, point->rpm);
    int textPosX = point->x - 20;
    int textPosY = point->y / HEIGHT > 0.6f ? point->y - 60 : point->y + 60;
    DrawText(pointInfoBuf, textPosX, textPosY, 18, WHITE);
}

void ProcessPoints(void)
{
    for (int pointi = 0; pointi < pointCount; pointi++) {
        Point point = points[pointi];
        Vector2 center = { .x = point.x, .y = point.y };
        bool collision = CheckCollisionPointCircle(GetMousePosition(), center, POINT_SIZE);
        if (!collision) continue;
        ShowPointDetails(&point);
    }
}

int main(int argc, char *argv[])
{
    //if (LoadSamples("total_results.tmp") != 0) {
    //    fprintf(stderr, "ERROR: could not load samples at %s", OUTPUT_FILE);
    //    exit(1);
    //}
    //CompressSamples();
    //SetPointsScreenCoords();

    //for (int i = 0; i < pointCount; i++) {
    //    printf("%f, %f\n", points[i].t, points[i].rpm);
    //} 

    //return 0;

    if (argc < 2) {
        fprintf(stderr, "USAGE: %s dataset\n", argv[0]);
        exit(1);
    }
    const char *dataset = argv[1];

    CallPythonModule(dataset);
    if (LoadSamples(OUTPUT_FILE) != 0) {
        fprintf(stderr, "ERROR: could not load samples at %s", OUTPUT_FILE);
        exit(1);
    }
    CompressSamples();

    InitWindow(1120, 840, "Plotter");
    SetTargetFPS(20);

    while (!WindowShouldClose()) {
        BeginDrawing();
            RenderAxis();
            RenderPlot();
            ProcessPoints();
            ClearBackground(BLACK);
        EndDrawing();
    }

    return 0;
}
