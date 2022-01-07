import sys
import time

import ecal.core.core as ecal_core
from ecal.core.publisher import StringPublisher

def main():
  # print eCAL version and date
  print("eCAL {} ({})\n".format(ecal_core.getversion(), ecal_core.getdate()))
  
  # initialize eCAL API
  ecal_core.initialize(sys.argv, "multi_hello_snd")
  
  # set process state
  ecal_core.set_process_state(1, 1, "I feel good")

  # create publisher
  pub1 = StringPublisher("Hello1")
  pub2 = StringPublisher("Hello2")
  pub3 = StringPublisher("Hello3")
  msg = "HELLO WORLD"
  
  # send messages
  i = 0
  while ecal_core.ok():
    i = i + 1
    current_message = "{} {:6d}".format(msg, i)
    print("Sending: {}".format(current_message))
    pub1.send(current_message)
    pub2.send(current_message)
    pub3.send(current_message)
    time.sleep(0.01)
  
  # finalize eCAL API
  ecal_core.finalize()

if __name__ == "__main__":
  main()
