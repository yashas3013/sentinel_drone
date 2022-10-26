#!/usr/bin/env python3

'''

This python file runs a ROS-node of name drone_control which holds the position of e-Drone on the given dummy.
This node publishes and subsribes the following topics:

		PUBLICATIONS			SUBSCRIPTIONS
		/drone_command			/whycon/poses
		/alt_error				/pid_tuning_altitude
		/pitch_error			/pid_tuning_pitch
		/roll_error				/pid_tuning_roll
					
								

Rather than using different variables, use list. eg : self.setpoint = [1,2,3], where index corresponds to x,y,z ...rather than defining self.x_setpoint = 1, self.y_setpoint = 2
CODE MODULARITY AND TECHNIQUES MENTIONED LIKE THIS WILL HELP YOU GAINING MORE MARKS WHILE CODE EVALUATION.	
'''

# Importing the required libraries
from os import setpgid
from edrone_client.msg import *
from geometry_msgs.msg import PoseArray
from std_msgs.msg import Int16
from std_msgs.msg import Int64
from std_msgs.msg import Float64
from pid_tune.msg import PidTune
import math
import rospy
import time


class Edrone():
	"""docstring for Edrone"""
	def __init__(self):
		
		rospy.init_node('drone_control')	# initializing ros node with name drone_control

		# This corresponds to your current position of drone. This value must be updated each time in your whycon callback
		# [x,y,z]
		self.drone_position = [0.0,0.0,0.0]	

		# [x_setpoint, y_setpoint, z_setpoint]

		global waypoints,errors,err_pid
		waypoints = [[0,0,23],[2,0,23],[2,2,23],[-2,2,23], [-2,-2,23],[2,-2,23],[2,0,23],[0,0,23]] # whycon marker at the position of the dummy given in the scene. Make the whycon marker associated with position_to_hold dummy renderable and make changes accordingly
		errors = [0.5,0.5,0.5]
		err_pid = [0.0,0.0,0.0]
		self.waypoint_num=0

		#Declaring a cmd of message type edrone_msgs and initializing values
		self.cmd = edrone_msgs()
		self.cmd.rcRoll = 1500
		self.cmd.rcPitch = 1500
		self.cmd.rcYaw = 1500
		self.cmd.rcThrottle = 1500
		self.cmd.rcAUX1 = 1500
		self.cmd.rcAUX2 = 1500
		self.cmd.rcAUX3 = 1500
		self.cmd.rcAUX4 = 1500


		#initial setting of Kp, Kd and ki for [roll, pitch, throttle]. eg: self.Kp[2] corresponds to Kp value in throttle axis
		#after tuning and computing corresponding PID parameters, change the parameters
		# self.Kp = [240,240,240]
		# self.Ki = [57,57,57]
		# self.Kd = [134,134,134]
		self.Kp = [0,0,24]
		self.Ki = [0,0,1]
		self.Kd = [0,0,35]
		self.prev_time = [0.0,0.0,0.0]
		self.prev_error = [0.0,0.0,0.0]
		self.e_integral = [0.0,0.0,0.0]
		self.sample_time = 0.060
	

		# Publishing /drone_command, /alt_error, /pitch_error, /roll_error
		self.command_pub = rospy.Publisher('/drone_command', edrone_msgs, queue_size=1)
		self.alt_error_pub = rospy.Publisher('/alt_error',Float64,queue_size=1)
		self.pitch_error_pub = rospy.Publisher('/pitch_error',Float64,queue_size=1)
		self.roll_error_pub = rospy.Publisher('/roll_error',Float64,queue_size=1)

		# Subscribing to /whycon/poses, /pid_tuning_altitude, /pid_tuning_pitch, pid_tuning_roll
		rospy.Subscriber('whycon/poses', PoseArray, self.whycon_callback)
		# rospy.Subscriber('/pid_tuning_altitude',PidTune,self.altitude_set_pid)
		# rospy.Subscriber('/pid_tuning_pitch',PidTune,self.pitch_set_pid)
		# rospy.Subscriber('/pid_tuning_roll',PidTune,self.roll_set_pid)
		rospy.Subscriber('/goal_post',PoseArray,)
  
		self.arm() 


	# Disarming condition of the drone
	def go_to_goal():
		pass
	def disarm(self):
		self.cmd.rcAUX4 = 1100
		self.command_pub.publish(self.cmd)
		rospy.sleep(1)


	# Arming condition of the drone : Best practise is to disarm and then arm the drone.
	def arm(self):

		self.disarm()

		self.cmd.rcRoll = 1500
		self.cmd.rcYaw = 1500
		self.cmd.rcPitch = 1500
		self.cmd.rcThrottle = 1000
		self.cmd.rcAUX4 = 1500
		self.command_pub.publish(self.cmd)	# Publishing /drone_command
		rospy.sleep(1)



	# Whycon callback function
	# The function gets executed each time when /whycon node publishes /whycon/poses 
	def whycon_callback(self,msg):
		self.drone_position[0] = msg.poses[0].position.x
		self.drone_position[1] = msg.poses[0].position.y
		self.drone_position[2] = msg.poses[0].position.z


	def set_pid_const(self):
		# self.Kp[2] = 240*0.06
		# self.Ki[2] = 103*0.0000000000001
		# self.Kd[2] = 66*0.3

		# self.Kp[0] = 240*0.06
		# self.Ki[0] = 57*0.0000000000001
		# self.Kd[0] = 66*0.3

		# self.Kp[1] = 240*0.06
		# self.Ki[1] = 57*0.0000000000001
		# self.Kd[1] = 66*0.3
		self.Kp[2] = 194*0.05
		self.Ki[2] = 99*0.0000000000005
		self.Kd[2] = 35*0.5

		self.Kp[0] = 230*0.05
		self.Ki[0] = 340*0.0000000000005
		self.Kd[0] = 88*0.5

		self.Kp[1] = 919*0.05
		self.Ki[1] = 88*0.0000000000005
		self.Kd[1] = 88*0.5


	# Callback function for /pid_tuning_altitude
	# This function gets executed each time when /tune_pid publishes /pid_tuning_altitude
	def altitude_set_pid(self,alt):
		self.Kp[2] = alt.Kp * 0.06 # This is just for an example. You can change the ratio/fraction value accordingly
		self.Ki[2] = alt.Ki * 0.00000000000001
		self.Kd[2] = alt.Kd * 0.5
		# print(self.Ki)
	def pitch_set_pid(self,pitch):
		self.Kp[1] = pitch.Kp * 0.06
		self.Ki[1] = pitch.Ki * 0.0000000000001
		self.Kd[1] = pitch.Kd * 0.3 
	def roll_set_pid(self,roll):
		self.Kp[0] = roll.Kp * 0.06
		self.Ki[0] = roll.Ki * 0.0000000000001
		self.Kd[0] = roll.Kd * 0.03 
	
	#----------------------------Define callback function like altitide_set_pid to tune pitch, roll--------------


	def calc_errors(self,i,errors):
		current_time = time.time()
		del_time = current_time - self.prev_time[i]
		del_error = errors[i] - self.prev_error[i]
		# print(del_time)
		if del_time >= self.sample_time:
			self.e_P = self.Kp[i]* errors[i]
			self.e_integral[i] += errors[i]*del_time

		self.Dterm = 0.0
		if del_time>0:
			self.Dterm = del_error/del_time
		self.prev_time[i] = current_time
		self.prev_error[i] = errors[i]
		return self.e_P + (self.Ki[i]*self.e_integral[i]) + (self.Kd[i]*self.Dterm)


		
	def pid(self):

		self.set_pid_const()
  
		setpoint=waypoints[self.waypoint_num]
		num_of_waypoints=len(waypoints)
  
		errors[0] = self.drone_position[0] - setpoint[0] # len 3
		errors[1] = self.drone_position[1] - setpoint[1]
		errors[2] = self.drone_position[2] - setpoint[2]
		# print(errors)
  
	
		for i in range(0,len(errors)):
			err_pid[i] = self.calc_errors(i,errors)			
		# print(err_pid)
  
		if((abs(errors[0])<0.04 and abs(errors[1])<0.04 and abs(errors[2])<0.04)):
			if self.waypoint_num<num_of_waypoints-1:
				self.waypoint_num+=1
				print("switch")
  
		self.cmd.rcRoll = int(1500 - err_pid[0])
		self.cmd.rcPitch = int(1500 + err_pid[1])
		self.cmd.rcThrottle = int(1500 + err_pid[2])
		# print(self.cmd)
  
		if self.cmd.rcRoll>1900: #integral windup
			self.cmd.rcRoll = 1900
		if self.cmd.rcPitch>1900:
			self.cmd.rcPitch = 1900
		if self.cmd.rcThrottle>1900:
			self.cmd.rcThrottle = 1900
		# print(self.cmd)

	#------------------------------------------------------------------------------------------------------------------------
		self.alt_error_pub.publish(errors[2])
		self.pitch_error_pub.publish(errors[1])
		self.roll_error_pub.publish(errors[0])
		# self.arm()
		self.command_pub.publish(self.cmd)




if __name__ == '__main__':

	e_drone = Edrone()
	r = rospy.Rate(4) 
	while not rospy.is_shutdown():
		e_drone.pid()
		r.sleep()