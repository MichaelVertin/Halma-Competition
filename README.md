# Running the Program

## Requirements
- Python 3.x
- tkinter

## Execution
Run the script from the command line:

```
python halma.py
```

This will open a new game window. The AI player controls the green pieces and the user player controls the blue pieces. 

To do a turn, select a blue piece. After, this will display yellow squares on the board where the piece can be placed. Click on one of these yellow squares to move the piece to that location. Then wait for the AI to do its turn. 

---

## Project Background
This AI was developed for the CS470 Halma AI Tournament, where each student submission played timed matches in a bracket format. My implementation incorporates two main enhancements aimed at maximizing search depth and efficiency within the given time limit.

**Result:**
- Increased search depth to 5–7 from an expected depth of <= 4.  
- Used **100-280%** more of the available 20 seconds (10-19s vs <5).


# Enhancement 1: Optimize alpha-beta
Alpha-beta pruning disables searching through possibilities that are irrational for players to choose due to better options. \
With the options to iterate through not being in a particular order, the system will likely not reach the best solution until many significantly worse ones are analyzed. \
Because many moves involve immediate negative progress, these moves are much less much less likely to result in the optimal move. By telling the algorithm to search through moves with immediate positive progress before moves with immediate negative progress, the pruning algorithm can identify optimal solutions almost immediately. \
The submitted project performs a shallow pre-sort on the possible moves before recursing by sorting each option based on how that option would impact the score. This will tend to increase the alpha and beta requirements sooner, resulting in more content being pruned. Additionally, it places the options that are least likely to be effective at the end, so an early exit due to lack of time is less likely to miss the best solution. 

# Enhancement 2: Dynamic Fractional Depth
The alpha-beta algorithm uses a fixed depth that represents how many future turns it attempts to predict. However, in the competition, the requirements were time-based, such that the system must select a turn within X seconds. \
To maximize the usage of allowed resources, this implementation included a getDepthFromTimes function that adjusted the depth with the intent of using 80% of the available time. The returned value was based on the amount of time used, the current depth, the progress made in the last decision, and the amount of children in the first iteration. It worked by converting the depth into an approximation of how many nodes were completed, used this to identify how many nodes it should attempt to complete, and converted this back into a depth. \
The implementation also mocked partial depth by using random numbers to determine if it should continue searching. This improves the accuracy of the depth prediction mentioned above, and provides a significant advantage over other submissions as it allows the program to use the full allotted time. \
Systems with different constants competed against each other to identify the optimal constants for this project. \
The code for this can be found in the "TIME_MANAGEMENT" section. 
