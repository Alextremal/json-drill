#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <raylib.h>

#define WIDTH 1120
#define HEIGHT 840
#define PLOT_MARGIN 50

#define MAX_SAMPLES 200
#define MEASURE_COUNT 10
#define PIXELS_PER_MEASURE (WIDTH / MEASURE_COUNT)

#define PYTHON_MODULE_PATH "../preprocessor/preprocessor.py"
#define OUTPUT_FILE        "./total_results.txt"

typedef struct {
    int x, y;
} Sample;

// TODO: Allocate memory for samples dynamically
Sample samples[MEASURE_COUNT] = {0};
int lower_y, upper_y;
int time_span;

// Convert from [lower_y..upper_y] to [PLOT_MARGIN..HEIGHT-PLOT_MARGIN]
int Screen(int y)
{
    // [lower_y..upper_y]   - lower_y
    // [0..upper_y-lower_y] / upper_y-lower_y
    // [0..1] * HEIGHT
    //return (1 - ((float) y / 9)) * (HEIGHT - 2*PLOT_MARGIN) + PLOT_MARGIN;
    return (1 - ((float) (y - lower_y) / (upper_y-lower_y))) * (HEIGHT - 2*PLOT_MARGIN) + PLOT_MARGIN;
}

void GenerateSamples(void)
{
    for (int i = 0; i < MEASURE_COUNT; i++) {
        samples[i] = (Sample) {
            .x = i,
            .y = rand()%10
        };
    }
}

void RenderAxis(void)
{
    // Vertical
    DrawLine(PLOT_MARGIN, HEIGHT-PLOT_MARGIN, PLOT_MARGIN, PLOT_MARGIN, WHITE);    
    // Horizontal
    DrawLine(PLOT_MARGIN, HEIGHT-PLOT_MARGIN, WIDTH-PLOT_MARGIN, HEIGHT-PLOT_MARGIN, WHITE);    
}

void RenderPlot(void)
{
    Sample firstSample = samples[0];
    Vector2 firstPoint = {
        .x = PIXELS_PER_MEASURE * firstSample.x + PLOT_MARGIN, // TODO: respect right margin too 
        .y = Screen(firstSample.y)
    };
    DrawCircleV(firstPoint, 5, RED);
    for (int i = 1; i < MEASURE_COUNT; i++) {
        Sample secondSample = samples[i];
        Vector2 secondPoint = {
            .x = PIXELS_PER_MEASURE * secondSample.x + PLOT_MARGIN, // TODO: respect right margin too 
            .y = Screen(secondSample.y)
        };
        DrawCircleV(secondPoint, 5, RED);
        DrawLineV(firstPoint, secondPoint, RED);
        firstPoint = secondPoint;
    }
}

// TODO:
// We assume we have MEASURE_COUNT number of values in the file;
// Handle errors properly.
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
    
    if (fscanf(f, "%d", &time_span) != 1)
        return -1;
    if (fscanf(f, "%d%d", &lower_y, &upper_y) != 2)
        return -1;
    // Advance to the next line
    while ((c = fgetc(f)) != '\n' && c != EOF)
        continue;

    while (fscanf(f, "%d%d", &sample_buf.x, &sample_buf.y) == 2) {
        if (samplei >= MEASURE_COUNT)
            break;
        samples[samplei++] = sample_buf;
        // Advance to the next line
        while ((c = fgetc(f)) != '\n' && c != EOF)
            continue;
    }
    return 0;
}

void PrepareData(const char *input_file)
{
    char python_call_cmd[128];
    snprintf(python_call_cmd, 128,
             "python %s %s raw %s", PYTHON_MODULE_PATH, input_file, OUTPUT_FILE);
    printf("%s\n", python_call_cmd);
    system(python_call_cmd); // TODO: Check for errors
    if (LoadSamples(OUTPUT_FILE) != 0) {
        fprintf(stderr, "ERROR: could not load samples at %s", OUTPUT_FILE);
        exit(1);
    }
}

// Compress samples so their amount doesn't exceed MEASURE_COUNT
void CompressSamples(void)
{
    int batch_size = time_span / MEASURE_COUNT; // TODO: Handle the possible remainder

}

int main(int argc, char *argv[])
{
    LoadSamples("total_results.txt");

    return 0;

    if (argc < 2) {
        fprintf(stderr, "USAGE: %s dataset\n", argv[0]);
        exit(1);
    }
    const char *dataset = argv[1];

    PrepareData(dataset);

    InitWindow(1120, 840, "Plotter");
    SetTargetFPS(20);

    while (!WindowShouldClose()) {
        BeginDrawing();
            RenderAxis();
            RenderPlot();
            //ClearBackground(RED);
        EndDrawing();
    }

    return 0;
}
