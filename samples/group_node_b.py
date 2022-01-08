import sys
import time

import ecal.core.core as ecal_core

def main():
  # print eCAL version and date
  print("eCAL {} ({})\n".format(ecal_core.getversion(), ecal_core.getdate()))
  
  # initialize eCAL API
  ecal_core.initialize(sys.argv, "group_node_b")
  
  # set process state
  ecal_core.set_process_state(1, 1, "I feel good")

  # define message callback
  def callback(tname, msg, snd_time):
    print("Received: %s."%(msg));

  # create publisher and subscriber
  pub_l = []
  for s in ['topic_b1', 'topic_b2', 'topic_b3','topic_b4',]:
    pub = ecal_core.publisher(s, s + '_type')
    pub_l.append(pub)

  sub_l = []
  for s in ['topic_a1', 'topic_a2', 'topic_c1','topic_c3',]:
    sub = ecal_core.subscriber(s)
    sub.set_callback(callback)
    sub_l.append(sub)
  
  # send messages
  while ecal_core.ok():
    for pub in pub_l:
      pub.send(("Message from %s."%(pub.tname)).encode());
    time.sleep(0.01)
  
  # finalize eCAL API
  ecal_core.finalize()

if __name__ == "__main__":
  main()
