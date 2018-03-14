#!/usr/bin/env python

# Import modules
import numpy as np
import sklearn
from sklearn.preprocessing import LabelEncoder
import pickle
from sensor_stick.srv import GetNormals
from sensor_stick.features import compute_color_histograms
from sensor_stick.features import compute_normal_histograms
from visualization_msgs.msg import Marker
from sensor_stick.marker_tools import *
from sensor_stick.msg import DetectedObjectsArray
from sensor_stick.msg import DetectedObject
from sensor_stick.pcl_helper import *

import rospy
import tf
from geometry_msgs.msg import Pose
from std_msgs.msg import Float64
from std_msgs.msg import Int32
from std_msgs.msg import String
from pr2_robot.srv import *
from rospy_message_converter import message_converter
import yaml


# Helper function to get surface normals
def get_normals(cloud):
    get_normals_prox = rospy.ServiceProxy('/feature_extractor/get_normals', GetNormals)
    return get_normals_prox(cloud).cluster

# Helper function to create a yaml friendly dictionary from ROS messages
def make_yaml_dict(test_scene_num, arm_name, object_name, pick_pose, place_pose):
    yaml_dict = {}
    yaml_dict["test_scene_num"] = test_scene_num.data
    yaml_dict["arm_name"]  = arm_name.data
    yaml_dict["object_name"] = object_name.data
    yaml_dict["pick_pose"] = message_converter.convert_ros_message_to_dictionary(pick_pose)
    yaml_dict["place_pose"] = message_converter.convert_ros_message_to_dictionary(place_pose)
    return yaml_dict

# Helper function to output to yaml file
def send_to_yaml(yaml_filename, dict_list):
    data_dict = {"object_list": dict_list}
    with open(yaml_filename, 'w') as outfile:
        yaml.dump(data_dict, outfile, default_flow_style=False)

# Callback function for your Point Cloud Subscriber
def pcl_callback(pcl_msg):

# Exercise-2 TODOs:

    # TODO: Convert ROS msg to PCL data
    cloud = ros_to_pcl(pcl_msg)

    # TODO: Statistical Outlier Filtering
    # Much like the previous filters, we start by creating a filter object:
    outlier_filter = cloud.make_statistical_outlier_filter()

    # Set the number of neighboring points to analyze for any given point
    outlier_filter.set_mean_k(1)

    # Set threshold scale factor
    x = 0.04

    # Any point with a mean distance larger than global (mean distance+x*std_dev) will be considered outlier
    outlier_filter.set_std_dev_mul_thresh(x)

    # Finally call the filter function for magic
    outlier_filtered = outlier_filter.filter()

    # TODO: Voxel Grid Downsampling
    vox = outlier_filtered.make_voxel_grid_filter()
    LEAF_SIZE = 0.01
    vox.set_leaf_size(LEAF_SIZE, LEAF_SIZE, LEAF_SIZE)
    vox_filtered = vox.filter()

    # TODO: PassThrough Filter
    passthrough_z = vox_filtered.make_passthrough_filter()
    filter_axis = 'z'
    passthrough_z.set_filter_field_name(filter_axis)
    axis_min = 0.605
    axis_max = 1.1
    passthrough_z.set_filter_limits(axis_min, axis_max)
    pass_filtered_z = passthrough_z.filter()

    passthrough_y = pass_filtered_z.make_passthrough_filter()
    filter_axis = 'y'
    passthrough_y.set_filter_field_name(filter_axis)
    axis_min = -0.40
    axis_max = 0.40
    passthrough_y.set_filter_limits(axis_min, axis_max)
    pass_filtered_y = passthrough_y.filter()

    # TODO: RANSAC Plane Segmentation
    seg = pass_filtered_y.make_segmenter()
    seg.set_model_type(pcl.SACMODEL_PLANE)
    seg.set_method_type(pcl.SAC_RANSAC)
    max_distance = 0.005
    seg.set_distance_threshold(max_distance)
    inliers, coefficients = seg.segment()

    # TODO: Extract inliers and outliers
    cloud_table = pass_filtered_y.extract(inliers, negative=False)
    cloud_objects = pass_filtered_y.extract(inliers, negative=True)

    # TODO: Euclidean Clustering
    white_cloud = XYZRGB_to_XYZ(cloud_objects)
    tree = white_cloud.make_kdtree()

    # TODO: Create Cluster-Mask Point Cloud to visualize each cluster separately
    ec = white_cloud.make_EuclideanClusterExtraction()
    ec.set_ClusterTolerance(0.02)
    ec.set_MinClusterSize(25)
    ec.set_MaxClusterSize(5000)
    ec.set_SearchMethod(tree)

    cluster_indices = ec.Extract()

    #Assign a color corresponding to each segmented object in scene
    cluster_color = get_color_list(len(cluster_indices))

    color_cluster_point_list = []

    for j, indices in enumerate(cluster_indices):
        for i, indice in enumerate(indices):
            color_cluster_point_list.append([white_cloud[indice][0],
                                            white_cloud[indice][1],
                                            white_cloud[indice][2],
                                             rgb_to_float(cluster_color[j])])

    #Create new cloud containing all clusters, each with unique color
    cluster_cloud = pcl.PointCloud_PointXYZRGB()
    cluster_cloud.from_list(color_cluster_point_list)

    # TODO: Convert PCL data to ROS messages
    ros_outlier_cloud = pcl_to_ros(outlier_filtered)
    ros_vox_cloud = pcl_to_ros(vox_filtered)
    ros_pass_cloud = pcl_to_ros(pass_filtered_z)
    ros_pass_cloud_y = pcl_to_ros(pass_filtered_y)
    ros_cluster_cloud = pcl_to_ros(cluster_cloud)
    ros_cloud_objects = pcl_to_ros(cloud_objects)
    ros_cloud_table = pcl_to_ros(cloud_table)

    # TODO: Publish ROS messages
    pcl_outlier_pub.publish(ros_outlier_cloud)
    pcl_vox_pub.publish(ros_vox_cloud)
    pcl_pass_pub.publish(ros_pass_cloud)
    pcl_pass_pub_y.publish(ros_pass_cloud_y)
    pcl_objects_pub.publish(ros_cloud_objects)
    pcl_table_pub.publish(ros_cloud_table)
    pcl_cluster_pub.publish(ros_cluster_cloud)

# Exercise-3 TODOs:

    # Classify the clusters! (loop through each detected cluster one at a time)
    detected_objects_labels = []
    detected_objects = []
        # Grab the points for the cluster

        # Compute the associated feature vector

        # Make the prediction

        # Publish a label into RViz

        # Add the detected object to the list of detected objects.

    for index, pts_list in enumerate(cluster_indices):
        # Grab the points for the cluster from the extracted outliers (cloud_objects)
        pcl_cluster = cloud_objects.extract(pts_list)
        # TODO: convert the cluster from pcl to ROS using helper function
        ros_cluster = pcl_to_ros(pcl_cluster)
        # Extract histogram features
        # TODO: complete this step just as is covered in capture_features.py
            # Extract histogram features
        chists = compute_color_histograms(ros_cluster, using_hsv=True)
        normals = get_normals(ros_cluster)
        nhists = compute_normal_histograms(normals)
        feature = np.concatenate((chists, nhists))
        #labeled_features.append([feature, model_name])
        # Make the prediction, retrieve the label for the result
        # and add it to detected_objects_labels list
        prediction = clf.predict(scaler.transform(feature.reshape(1,-1)))
        label = encoder.inverse_transform(prediction)[0]
        detected_objects_labels.append(label)

        # Publish a label into RViz
        label_pos = list(white_cloud[pts_list[0]])
        label_pos[2] += .4
        object_markers_pub.publish(make_label(label,label_pos, index))

        # Add the detected object to the list of detected objects.
        do = DetectedObject()
        do.label = label
        do.cloud = ros_cluster
        detected_objects.append(do)
    rospy.loginfo('Detected {} objects: {}'.format(len(detected_objects_labels), detected_objects_labels))

    # Publish the list of detected objects
    # This is the output you'll need to complete the upcoming project!
    detected_objects_pub.publish(detected_objects)
    # Publish the list of detected objects

    # Suggested location for where to invoke your pr2_mover() function within pcl_callback()
    # Could add some logic to determine whether or not your object detections are robust
    # before calling pr2_mover()
    try:
        pr2_mover(detected_objects)
    except rospy.ROSInterruptException:
        pass

# function to load parameters and request PickPlace service
def pr2_mover(object_list):
    # TODO: Initialize variables
    TEST_SCENE_NUM = Int32()
    OBJECT_NAME = String()
    WHICH_ARM = String()
    PICK_POSE = Pose()
    PLACE_POSE = Pose()
    dict_list = []

    # TODO: Get/Read parameters
    object_list_param = rospy.get_param('/object_list')
    dropbox = rospy.get_param('/dropbox')
    dropbox_green = None
    dropbox_red = None
    for i in range(len(dropbox)):
        if dropbox[i]['group'] == "green":
            dropbox_green = dropbox[i]
        elif dropbox[i]['group'] == "red":
            dropbox_red = dropbox[i]

    # TODO: Parse parameters into individual variables


    # TODO: Rotate PR2 in place to capture side tables for the collision map

    # TODO: Loop through the pick list
    for i in range(len(object_list_param)):
        obj_name = object_list_param[i]['name']
        object_group = object_list_param[i]['group']
        # TODO: Get the PointCloud for a given object and obtain it's centroid
        labels = []
        centroids = []
        for obj in object_list:
            if (obj_name == obj.label):
                labels.append(obj_name)
                points_arr = ros_to_pcl(obj.cloud).to_array()
                centroid = np.mean(points_arr, axis=0)[:3]
                centroid_scalar = [np.asscalar(centroid[0]),
                np.asscalar(centroid[1]),
                np.asscalar(centroid[2])]
                #centroids.append(np.asscalar(centroid))
                centroids.append(centroid_scalar)


        for i in range(len(labels)):
            # TODO: Create 'place_pose' for the object
            TEST_SCENE_NUM.data = 1
            OBJECT_NAME.data = labels[i]
            # TODO: Assign the arm to be used for pick_place
            if object_group == "green":
                WHICH_ARM.data = "right"
                PLACE_POSE.position.x = dropbox_green["position"][0]
                PLACE_POSE.position.y = dropbox_green["position"][1]
                PLACE_POSE.position.z = dropbox_green["position"][2]
            else:
                WHICH_ARM.data = "left"
                PLACE_POSE.position.x = dropbox_red["position"][0]
                PLACE_POSE.position.y = dropbox_red["position"][1]
                PLACE_POSE.position.z = dropbox_red["position"][2]
            PICK_POSE.position.x = centroids[i][0]
            PICK_POSE.position.y = centroids[i][1]
            PICK_POSE.position.z = centroids[i][2]
            # TODO: Create a list of dictionaries (made with make_yaml_dict()) for later output to yaml format
            yaml_dict = make_yaml_dict(TEST_SCENE_NUM,
                                       WHICH_ARM,
                                       OBJECT_NAME,
                                       PICK_POSE,
                                       PLACE_POSE)
            dict_list.append(yaml_dict)

    """
    for i in range(len(object_list_param)):

        pcl_collision_pub.publish()

        # Wait for 'pick_place_routine' service to come up
        rospy.wait_for_service('pick_place_routine')

        try:
            pick_place_routine = rospy.ServiceProxy('pick_place_routine', PickPlace)

            # TODO: Insert your message variables to be sent as a service request
            resp = pick_place_routine(TEST_SCENE_NUM,
                OBJECT_NAME,
                WHICH_ARM,
                PICK_POSE,
                PLACE_POSE)

            print ("Response: ",resp.success)

        except rospy.ServiceException, e:
            print "Service call failed: %s"%e
    """
    # TODO: Output your request parameters into output yaml file
    #send_to_yaml("output_1.yaml", dict_list)
    #send_to_yaml("output_2.yaml", dict_list)
    send_to_yaml("output_3.yaml", dict_list)
    #send_to_yaml("output_4.yaml", dict_list)

if __name__ == '__main__':

    # TODO: ROS node initialization
    rospy.init_node('clustering', anonymous=True)
    # TODO: Create Subscribers
    pcl_sub = rospy.Subscriber("/pr2/world/points", pc2.PointCloud2, pcl_callback, queue_size=1)
    # TODO: Create Publishers
    object_markers_pub = rospy.Publisher("/object_markers", Marker, queue_size=1)
    detected_objects_pub = rospy.Publisher("/detected_objects", DetectedObjectsArray, queue_size=1)

    pcl_outlier_pub = rospy.Publisher("/pcl_outlier", PointCloud2, queue_size=1)
    pcl_vox_pub = rospy.Publisher("/pcl_vox", PointCloud2, queue_size=1)
    pcl_pass_pub = rospy.Publisher("/pcl_pass", PointCloud2, queue_size=1)
    pcl_pass_pub_y = rospy.Publisher("/pcl_pass_y", PointCloud2, queue_size=1)
    pcl_objects_pub = rospy.Publisher("/pcl_objects", PointCloud2, queue_size=1)
    pcl_table_pub = rospy.Publisher("/pcl_table", PointCloud2, queue_size=1)
    pcl_cluster_pub = rospy.Publisher("/pcl_cluster", PointCloud2, queue_size=1)
    pcl_collision_pub = rospy.Publisher("/pr2/3D_map/points", PointCloud2, queue_size=1)
    # TODO: Load Model From disk
    model = pickle.load(open('model.sav', 'rb'))
    clf = model['classifier']
    encoder = LabelEncoder()
    encoder.classes_ = model['classes']
    scaler = model['scaler']
    # Initialize color_list
    get_color_list.color_list = []

    # TODO: Spin while node is not shutdown
    while not rospy.is_shutdown():
        rospy.spin()

    # TODO: ROS node initialization

    # TODO: Create Subscribers

    # TODO: Create Publishers

    # TODO: Load Model From disk

    # Initialize color_list
    #get_color_list.color_list = []

    # TODO: Spin while node is not shutdown
