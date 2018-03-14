## Project: 3D Perception Pick & Place


---


[//]: # (Image References)

[image1]: ./image/world_points.jpg "World Points"
[image2]: ./image/outlier.jpg "Outlier"
[image3]: ./image/voxel_downsampling.jpg "Voxel Downsampling"
[image4]: ./image/passthrough.jpg "Pass Through"
[image5]: ./image/ransac_objects.jpg "RANSAC Objects"
[image6]: ./image/ransac_table.jpg "RANSAC Table"
[image7]: ./image/clustering.jpg "Clustering"
[image8]: ./image/confusion_matrix1.jpg "Confusion Matrix 1"
[image9]: ./image/confusion_matrix2.jpg "Confusion Matrix 2"
[image10]: ./image/confusion_matrix3.jpg "Confusion Matrix 3"
[image11]: ./image/with3.png "Image with the target 3"
[image12]: ./image/loss_graph.png "Loss Graph"
[image13]: ./image/IoU_graph.png "IoU Graph"

# Required Steps for a Passing Submission:
1. Extract features and train an SVM model on new objects (see `pick_list_*.yaml` in `/pr2_robot/config/` for the list of models you'll be trying to identify).
2. Write a ROS node and subscribe to `/pr2/world/points` topic. This topic contains noisy point cloud data that you must work with.
3. Use filtering and RANSAC plane fitting to isolate the objects of interest from the rest of the scene.
4. Apply Euclidean clustering to create separate clusters for individual items.
5. Perform object recognition on these objects and assign them labels (markers in RViz).
6. Calculate the centroid (average in x, y and z) of the set of points belonging to that each object.
7. Create ROS messages containing the details of each object (name, pick_pose, etc.) and write these messages out to `.yaml` files, one for each of the 3 scenarios (`test1-3.world` in `/pr2_robot/worlds/`).  [See the example `output.yaml` for details on what the output should look like.](https://github.com/udacity/RoboND-Perception-Project/blob/master/pr2_robot/config/output.yaml)
8. Submit a link to your GitHub repo for the project or the Python code for your perception pipeline and your output `.yaml` files (3 `.yaml` files, one for each test world).  You must have correctly identified 100% of objects from `pick_list_1.yaml` for `test1.world`, 80% of items from `pick_list_2.yaml` for `test2.world` and 75% of items from `pick_list_3.yaml` in `test3.world`.
9. Congratulations!  Your Done!

# Extra Challenges: Complete the Pick & Place
7. To create a collision map, publish a point cloud to the `/pr2/3d_map/points` topic and make sure you change the `point_cloud_topic` to `/pr2/3d_map/points` in `sensors.yaml` in the `/pr2_robot/config/` directory. This topic is read by Moveit!, which uses this point cloud input to generate a collision map, allowing the robot to plan its trajectory.  Keep in mind that later when you go to pick up an object, you must first remove it from this point cloud so it is removed from the collision map!
8. Rotate the robot to generate collision map of table sides. This can be accomplished by publishing joint angle value(in radians) to `/pr2/world_joint_controller/command`
9. Rotate the robot back to its original state.
10. Create a ROS Client for the “pick_place_routine” rosservice.  In the required steps above, you already created the messages you need to use this service. Checkout the [PickPlace.srv](https://github.com/udacity/RoboND-Perception-Project/tree/master/pr2_robot/srv) file to find out what arguments you must pass to this service.
11. If everything was done correctly, when you pass the appropriate messages to the `pick_place_routine` service, the selected arm will perform pick and place operation and display trajectory in the RViz window
12. Place all the objects from your pick list in their respective dropoff box and you have completed the challenge!
13. Looking for a bigger challenge?  Load up the `challenge.world` scenario and see if you can get your perception pipeline working there!

## [Rubric](https://review.udacity.com/#!/rubrics/1067/view) Points
### Here I will consider the rubric points individually and describe how I addressed each point in my implementation.

---

### Exercise 1, 2 and 3 pipeline implemented

#### 1. Complete Exercise 1 steps. Pipeline for filtering and RANSAC plane fitting implemented.

##### 1. Outlier Filter
Statistical outlier filter applied to remove the outlier points. The mean k parameter was set to 1 and the std_dev_mul_thresh parameter was set to 0.04. The images before and after the outlier filter are given below


Before Outlier


![alt text][image1]


After Outlier


![alt text][image2]


##### 2. Voxel Downsampling
Allied voxel_grid_filter with LEAF_SIZE = 1. In order to decrease the size and the complexity of the point cloud.

Image after voxel filter is given below:


![alt text][image3]


##### 3. Pass Through Filter
In order to get the region of interest, specific parts the point cloud were cropped.
* Along z-axis the range was between 0.605 and 1.1.
* Along y-axis the range was between -0.4 and 0.4.

Image after passthrough filter is given below:


![alt text][image4]


##### 4. RANSAC
RANSAC Plane Segmentation was applied to segment the point clouds of the table and the objects. The max distance parameter was set to 0.005. After the segmentation these point clouds were separated. The output image of the objects are as follows:


![alt text][image5]


The image of the point clouds of the table:


![alt text][image6]


#### 2. Complete Exercise 2 steps: Pipeline including clustering for segmentation implemented.
##### 1. Euclidean Clustering
Using Euclidean Clustering, the objects were clustered. The parameters are as follows:
* ClusterTolerance: 0.02
* MinClusterSize: 25
* MaxClusterSize: 5000


The image of clustered point clouds are as follows:


![alt text][image7]


#### 3. Complete Exercise 3 Steps.  Features extracted and SVM trained.  Object recognition implemented.
##### 1. Train SVM
###### General Settings
Image converted to HSV color space.
The bins_range for color histogram was (0,256)

###### 1. SVM 1
Color histogram had 32 bins.
Normal histogram had 32 bins.
The bins_range of the Normal Histogram was (0,256).
Number of samples from each object was 100.
The SVM kernel was linear (best performing kernel for this dataset).


Despite the wrong bins_range parameter, this SVM performed the best. The image of the confusion matrix of this model is given below.


![alt text][image8]


The extracted features data are located in training_set.sav file.
The generated model is stored in the model.sav file.


##### 2. SVM 2
Color histogram had 64 bins.
Normal histogram had 64 bins.
The bins_range of the Normal Histogram was corrected to (-1,1).
Number of samples from each object was 200.
The SVM kernel was rbf (best performing kernel for this dataset).
The image of the confusion matrix of this model is given below.


![alt text][image9]


The extracted features data are located in models/training_set_2_200_64.sav file.
The generated model is stored in the models/training_set_2_200_64.sav file.

##### 3. SVM 3
Color histogram had 32 bins.
Normal histogram had 32 bins.
The bins_range of the Normal Histogram was corrected to (-1,1).
Number of samples from each object was 100.
The SVM kernel was rbf (best performing kernel for this dataset).
The image of the confusion matrix of this model is given below.


![alt text][image9]


The extracted features data are located in models/training_set_3_100_32.sav file.
The generated model is stored in the models/training_set_3_100_32.sav file.

### Pick and Place Setup
#### 1. For all three tabletop setups (`test*.world`), perform object recognition, then read in respective pick list (`pick_list_*.yaml`). Next construct the messages that would comprise a valid `PickPlace` request output them to `.yaml` format.

The output .yaml files output_1.yaml, output_2.yaml, output_3.yaml are provided under the outputs folder, for the test1.world, test2.world, test3.world respectively.


### Future Enhancements
Due to the time limitations, the pick and place part was not implemented. Therefore, the first enhancement to work on is the extra challanges part.

Currently, the robot can only detect objects directly in front of it. For the situations like in the challenge.world, the robot needs to turn and capture new images to detect all of the objects. This is an example of where this implementation fail.

Furthermore, the object recognition algorithm does not work well. In the 3rd test world, it misclassified the glue behind of the notebook as sticky notes.