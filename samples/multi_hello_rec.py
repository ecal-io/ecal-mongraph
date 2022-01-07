import sys
import time

import ecal.core.core as ecal_core
from ecal.core.subscriber import StringSubscriber

# eCAL receive callback
def callback(topic_name, msg, time):
  print("Received:  {} ms   {}".format(time, msg))

def main():  
  # print eCAL version and date
  print("eCAL {} ({})\n".format(ecal_core.getversion(), ecal_core.getdate()))
  
  # initialize eCAL API
  ecal_core.initialize(sys.argv, "multi_hello_rec")
  
  # set process state
  ecal_core.set_process_state(1, 1, "I feel good")

  # create subscriber and connect callback
  sub1 = StringSubscriber("Hello1")
  sub2 = StringSubscriber("Hello2")
  sub3 = StringSubscriber("Hello3")
  sub1.set_callback(callback)
  sub2.set_callback(callback)
  sub3.set_callback(callback)
  
  # idle main thread
  while ecal_core.ok():
    time.sleep(0.1)
  
  # finalize eCAL API
  ecal_core.finalize()
  
if __name__ == "__main__":
  main()
