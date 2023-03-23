import csv
import os
import threading
import customtkinter as ctk
from tkinter import filedialog

import cv2
import mediapipe as mp
from PIL import Image, ImageTk

from copy import deepcopy

class PoseDetector():

    def __init__(self,mode=False,complexity=2,smoothlm=True,eseg=False,smooth=True,detectionCon=0.8,trackCon= 0.8):
        self.mode = mode
        self.complexity = complexity
        self.smoothlm = smoothlm
        self.eseg = eseg
        self.smooth = smooth
        self.detectionCon = detectionCon
        self.trackCon= trackCon
        self.mpDraw = mp.solutions.drawing_utils
        self.mpPose = mp.solutions.pose
        self.pose = self.mpPose.Pose( self.mode,self.complexity,self.smoothlm,self.eseg,self.smooth,self.detectionCon,self.trackCon)

    def find_pose(self,img,draw=True):
        imgRGB = cv2.cvtColor(img,cv2.COLOR_BGR2RGB)
        self.results = self.pose.process(imgRGB)
        if self.results.pose_landmarks:
            if draw:
                #self.mpDraw.plot_landmarks(self.results.pose_world_landmarks,self.mpPose.POSE_CONNECTIONS)
                self.mpDraw.draw_landmarks(img,self.results.pose_landmarks,self.mpPose.POSE_CONNECTIONS)
        return img
            
            
    def find_position(self,img,draw = True):
        lm_list=[]
        if self.results.pose_landmarks:
            for id,lm in enumerate(self.results.pose_landmarks.landmark):
                h,w,c = img.shape
                cx,cy = int(lm.x*w),int(lm.y*h)
                lm_list.append([id,lm.x,lm.y,lm.z, lm.visibility])
                cv2.circle(img,(cx,cy),2,(255,0,0),cv2.FILLED)
        lm_list.append([-1, -1, -1, -1, 0])
        return lm_list

class VideoPlayer:
    start_frame = 0
    current_frame = 0
    end_frame = 0
    
    def __init__(self, master):
        self.master = master
        self.master.title("Pratibimbha")

        self.detector = PoseDetector()
        self.csv_file = None
        self.csv_writer = None
        # Create a canvas for the video preview
        self.preview_canvas = ctk.CTkCanvas(self.master, width=640, height=480, background="black", highlightbackground="black")
        self.preview_canvas.pack()
        
        # Top Button Frame
        top_frame = ctk.CTkFrame(master)
        top_frame.pack( side = ctk.TOP )
        
        #Create the load button
        self.load_button = ctk.CTkButton(top_frame, text='Load Video', command=self.load_video)
        self.load_button.pack(padx = 3, pady=10,side=ctk.LEFT)

        #current frame count display variable
        self.frame_string = ctk.StringVar()
        self.frame_string.set("Frame: 0")
        text_frame = ctk.CTkFrame(master)
        text_frame.pack()
        self.current_frame_label = ctk.CTkLabel(text_frame, textvariable=self.frame_string)
        self.current_frame_label.pack(padx = 50, pady=2, side=ctk.LEFT)
        
        # mid Button Frame
        mid_frame = ctk.CTkFrame(master)
        mid_frame.pack( )
        
        #select output folder
        self.output_folder_button = ctk.CTkButton(mid_frame, text='Select Output Folder', command=self.select_folder)
        self.output_folder_button.pack(pady=10,side=ctk.TOP)
        
        #textfield for outputfile
        self.out_name = ctk.StringVar()
        self.out_name.set("Pose_Data.csv")

        self.out_name_label = ctk.CTkTextbox(mid_frame, height = 1, wrap = "none")
        self.out_name_label.pack(pady=10,side=ctk.BOTTOM)

        self.out_name_label.delete(1.0, ctk.END)
        self.out_name_label.insert("end-1c","./pose.csv")

        # Create the start frame slider
        self.start_slider = ctk.CTkSlider(self.master, from_=0, to=0, orientation=ctk.HORIZONTAL, width=500, command=self.update_start_frame)
        self.start_slider.pack()

        # Create the end frame slider
        self.end_slider = ctk.CTkSlider(self.master, from_=0, to=0, orientation=ctk.HORIZONTAL, width=500, command=self.update_end_frame)
        self.end_slider.pack()

        bottom_frame = ctk.CTkFrame(master)
        bottom_frame.pack( side = ctk.TOP )
        # Create a "Play" button
        self.play_button = ctk.CTkButton(bottom_frame, text="Play", command=self.start_video_thread)
        # Create the Stop button
        self.stop_button = ctk.CTkButton(bottom_frame, text="Stop", command=self.stop_video)

        # create a checkbox to toggle the pose detection
        self.display_pose = ctk.IntVar()
        self.display_pose_checkbox = ctk.CTkCheckBox(bottom_frame, text="Display Pose", variable=self.display_pose)
        self.display_pose_checkbox.pack(padx = 10, pady=10, side=ctk.LEFT)

        self.skip_video = ctk.IntVar()
        self.skip_video_checkbox = ctk.CTkCheckBox(bottom_frame, text="Skip Rendering", variable=self.skip_video)
        self.skip_video_checkbox.pack(padx = 10, pady=10, side=ctk.LEFT)


        self.play_button.pack(padx = 10, pady=10, side=ctk.LEFT)
        self.stop_button.pack(padx = 10, pady=10, side=ctk.LEFT)

        # Load the video file
        self.cap = cv2.VideoCapture("")

        # Initialize the video playing state
        self.playing = False
#####

    def select_folder(self):
        self.out_directory = filedialog.askdirectory()
        self.out_name_label.delete(1.0, ctk.END)
        if self.out_directory == "":
            self.out_name_label.insert("end-1c","./pose.csv")
        elif self.out_directory[-1] == '/':
            self.out_name_label.insert("end-1c",self.out_directory+"pose.csv")
        else:
            self.out_name_label.insert("end-1c",self.out_directory+"/pose.csv")
        print((self.out_name_label.get("1.0",ctk.END)))

    def load_video(self):
        # Open a file dialog to select the video file
        self.stop_video()
        cv2.waitKey(15)
        self.video_file = filedialog.askopenfilename()
        print(self.video_file )
        # Load the video file
        self.cap = cv2.VideoCapture(self.video_file)

        # Set the initial frame number to 0
        self.frame_num = 0

        # Set the default start and end frames
        self.start_frame = 0
        self.end_frame = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        print(self.start_frame,self.end_frame)
        # Set the maximum value of the sliders to the number of frames in the video
        self.start_slider.configure(to=self.end_frame)
        self.end_slider.configure(to=self.end_frame)
        self.start_slider.set(0)
        self.end_slider.set(self.end_frame)
        self.update_current_frame(0)
        self.play_video(update_preview=True)
    
    def update_current_frame(self,val):
        self.current_frame = val
        self.frame_string.set(f"Frame: {self.current_frame-1} / {self.end_frame}")
        # self.current_frame_label.setvar(name=f"Frame: {self.current_frame}")
        return

    def update_start_frame(self,val):
        # Update the start frame
        self.stop_video()
        #cv2.waitKey(15)
        self.start_frame = int(val)
        if self.end_frame < self.start_frame:
            self.end_frame = self.start_frame
            self.end_slider.set(self.start_frame)
        
        self.update_current_frame(int(val))
        self.play_video(update_preview=True)
            

        # Function to update the end frame slider
    def update_end_frame(self,val):
        # Update the end frame
        self.stop_video()
        #cv2.waitKey(15)
        self.end_frame = int(val)
        
        self.update_current_frame(self.end_frame)
        self.play_video(update_preview=True)        
        if self.end_frame < self.start_frame:
            self.start_frame = self.end_frame
            self.start_slider.set(self.end_frame)
        
        
####

    def start_video_thread(self):
        # Start the video playing thread
        self.video_thread = threading.Thread(target=self.play_video)
        self.video_thread.start()

    def play_video(self,update_preview = False):
        self.stop_video()
        cv2.waitKey(25)
        # Set the playing state to True
        self.playing = True
        # print(self.start_frame)
        if not update_preview:
            self.current_frame = self.start_frame
        self.cap.set(cv2.CAP_PROP_POS_FRAMES,self.current_frame)

        if self.start_frame < 0:
            return

        csv_file_name = str(self.out_name_label.get("1.0", ctk.END)).strip()

        # assuming the user has already set the path to where they want to store the file via the text box and then pressed the play button
        self.csv_file = open(csv_file_name, "w", newline="")
        self.csv_writer = csv.writer(self.csv_file)
        self.csv_writer.writerow(["index", "x", "y", "z", "vis"])

        # Loop through the frames and display them in the preview canvas
        while self.playing:
            # print(self.cap.get(cv2.CAP_PROP_POS_FRAMES),self.current_frame)
            if self.cap.get(cv2.CAP_PROP_POS_FRAMES)>self.end_frame:
                self.stop_video()
                break 
            # Read a frame from the video
            ret, frame = self.cap.read()

            # If the frame is read successfully, display it in the preview canvas
            if ret:
                # Resize the frame to fit within the canvas while maintaining aspect ratio
                canvas_width = self.preview_canvas.winfo_width()
                canvas_height = self.preview_canvas.winfo_height()
                frame_ratio = frame.shape[1] / frame.shape[0]
                canvas_ratio = canvas_width / canvas_height

                if frame_ratio > canvas_ratio:
                    # Fit to canvas width
                    new_height = int(canvas_width / frame_ratio)
                    frame = cv2.resize(frame, (canvas_width, new_height))
                else:
                    # Fit to canvas height
                    new_width = int(canvas_height * frame_ratio)
                    frame = cv2.resize(frame, (new_width, canvas_height))

                # Convert the frame to RGB color space and resize it to fit in the preview canvas
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                preview_height = self.preview_canvas.winfo_height()
                preview_width = int(frame.shape[1] * preview_height / frame.shape[0])
                # frame = cv2.resize(frame, (preview_width, preview_height))

                # Display the frame in the preview canvas
                img = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                # img = cv2.resize(img, (self.preview_canvas.winfo_width(), self.preview_canvas.winfo_height()))
                img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                original_img = deepcopy(img)
                img = self.detector.find_pose(img)
                lm_list = self.detector.find_position(img)
                if self.csv_writer != None:
                    for pt in lm_list:
                        self.csv_writer.writerow([pt[0],pt[1],pt[2],pt[3], pt[4]])
                if self.display_pose.get() == 0:
                    img = original_img
                if self.skip_video.get() == 0:
                    img = Image.fromarray(img)
                    img = ImageTk.PhotoImage(img)
                    self.preview_canvas.create_image(canvas_width//2, canvas_height//2, image=img)
                    self.preview_canvas.image = img

                # Wait for a short time to simulate real-time video playback
                #cv2.waitKey(15)

                self.update_current_frame(self.current_frame + 1)
            # If the frame cannot be read, stop the video preview
            else:
                self.stop_video()
                break
            if update_preview:
                self.stop_video()
                break

    def stop_video(self):
        # Set the playing state to False
        self.playing = False
        if self.csv_file != None:
            self.csv_file.close()
            self.csv_file = None
        self.csv_writer = None

    def __del__(self):
        self.stop_video()
        # Release the video file
        self.cap.release()

def main():
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("dark-blue")
    root = ctk.CTk()
    player = VideoPlayer(root)
    root.mainloop()

if __name__ == "__main__":
    main()