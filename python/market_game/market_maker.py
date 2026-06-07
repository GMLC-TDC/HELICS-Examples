import helics as h
from dataclasses import dataclass,field
import json
import random
import matplotlib.pyplot as plt
import sys
import argparse

from battery import Battery,check_valid,ensure_valid

# defining a house federate
      
@dataclass
class SubFed:
    battery:Battery=field(default_factory=Battery)
    input:h.HelicsInput=None
    totalCost:float=0.0
    hourCost:list[float]=field(default_factory=list)
    demand:list[float]=field(default_factory=lambda: [5] * 24)
    consume:list[float]=field(default_factory=list)
    name:str=""

def compute_new_price(total:float, feds:int)->float:
    if feds==0:
        return 0.1
    M=total/feds
    if M<3.0:
        price=0.1
    elif M<6.0:
        price=0.1+0.03*(M-3.0)
    elif M<9.0:
        price=0.19+0.1*(M-6.0)
    elif M<13.0:
        price=0.49+0.25*(M-9.0)
    else:
        price=1.49+1.0*(M-13.0)
    return price

def update_demand(type:str,fed:SubFed):
    if type=='random':
        elements=[random.random() for _ in range(24)]
        mult=120.0/sum(elements)
        fed.demand=[x*mult for x in elements]
    elif type=='spike':
        random_number = random.randint(0, 23)
        fed.demand=[4] * 24
        fed.demand[random_number]=28
    elif type=='dspike':
        random_number = random.randint(0, 23)
        fed.demand=[3] * 24
        fed.demand[random_number]+=24
        random_number = random.randint(0, 23)
        fed.demand[random_number]+=24
    elif type == 'profile1':
        fed.demand=[2, 1, 1, 1, 2, 4, 6, 8, 9, 7, 5, 4, 3, 4, 5, 7, 9, 12, 10, 7, 5, 4, 2,2]
    elif type == 'profile_solar':
        profile=[2, 2, 2, 2, 3, 4, 5, 2, -4, -6, -7, -8, -7, -6, -3, 1, 4, 8, 10, 11, 10, 7, 5, 3]
        fed.demand=[x*3.0 for x in profile]
    else:
        fed.demand=[5] * 24
   
   
parser = argparse.ArgumentParser(description="market maker federate commands")
parser.add_argument("--auto", action="store_true", default=False, help="run in auto mode")
parser.add_argument("--autobroker", action="store_true", default=False, help="enable local broker")
parser.add_argument("--broker", type=str, default="localhost", help="address of the broker")
parser.add_argument("--no-plot", action="store_true", default=False, help="skip showing plots at the end")
parser.add_argument("--profile", type=str, default="profile1", help="type of load profile to use: flat, spike, dspike, random, profile1, profile_solar")

args = parser.parse_args()

         
fedinfo = h.helicsCreateFederateInfo()
h.helicsFederateInfoSetCoreType(fedinfo,h.HELICS_CORE_TYPE_ZMQ_SS)
#depending on the setup this will need to be modified
h.helicsFederateInfoSetBroker(fedinfo,args.broker)

h.helicsFederateInfoSetTimeProperty(fedinfo, h.helics_property_time_period, 1.0)
h.helicsFederateInfoSetFlagOption(fedinfo,h.HELICS_FLAG_WAIT_FOR_CURRENT_TIME_UPDATE,True)

#set to whatever federate name you want
federate_name="market_maker_fed"
# create the federate using the federate Info structure

if args.autobroker:
    broker=h.helicsCreateBroker("zmqss","market_maker","--ipv4 -f1")

    print(f"broker created: address= {h.helicsBrokerGetAddress(broker)}")
market_maker=h.helicsCreateCombinationFederate(federate_name,fedinfo)

# register the price publication
price=market_maker.register_global_publication("price",h.HELICS_DATA_TYPE_DOUBLE,"$/kWh")

fedQuery=h.helicsCreateQuery("federation","federates")

if not args.auto:
    while True:
        if args.autobroker:
            results=h.helicsQueryBrokerExecute(fedQuery,broker)
        else:
            results=h.helicsQueryExecute(fedQuery,market_maker)
        index=0
        for fed in results:
            print(f"fed {index}:{fed}")
            index+=1
        res = input("enter i to start initialization: ")
        if res and res[0]=='i':
            break
        if res and res[0]=='q':
            h.helicsFederateDisconnect(market_maker)
            if args.autobroker:
                h.helicsBrokerDisconnect(broker)
            quit()
        
# Now enter initializing mode iterative
h.helicsFederateEnterInitializingModeIterative(market_maker)

if args.autobroker:
    results=h.helicsQueryBrokerExecute(fedQuery,broker)
else:
    results=h.helicsQueryExecute(fedQuery,market_maker)
feds=[]
#demandType='flat'
#demandType='spike'
#demandType='dspike'
#demandType='random'
#demandType='profile_solar'
demandType=args.profile
for fed in results:
    if fed==federate_name:
        continue
    print(f"fed {len(feds)}:{fed}")
    sf=SubFed(name=fed)
    if demandType !='flat':
        update_demand(demandType,sf)
    sf.input=h.helicsFederateRegisterSubscription(market_maker,sf.name+"/demand","kWh")
    h.helicsFederateSendCommand(market_maker,sf.name,json.dumps({"demand":sf.demand}))
    feds.append(sf)

h.helicsFederateEnterInitializingMode(market_maker)
num_feds=len(feds)
current_price=0.5
price.publish(current_price)
h.helicsFederateEnterExecutingMode(market_maker)
current_time=0
cprice=[]
loads=[]
while current_time<24:
    total_load=0
    hour=int(current_time)
    for fed in feds:
        penaltyCost=0
        load=h.helicsInputGetDouble(fed.input)
        warning=check_valid(load,fed.demand[hour], fed.battery)
        if warning:
            valid_load=ensure_valid(load,fed.demand[hour], fed.battery)
            penaltyCost=20*abs(load-valid_load)
            print(f"invalid demand received for fed {fed.name}={load} vs {valid_load} warning={warning}, recalculating with new value and assessing penalty={penaltyCost}")
            load=valid_load
       
        fed.battery.change(load-fed.demand[hour])
        fed.consume.append(load)
        fed.hourCost.append(load*current_price+penaltyCost)
        print(f"hr {hour}: federate {fed.name} using {load} scheduled {fed.demand[hour]} battery at {fed.battery.energy} cost={load*current_price+penaltyCost}")
        total_load+=load
    loads.append(total_load)
    print(f"hr {hour}: total load {total_load} new  price = {current_price} ")
    current_price=compute_new_price(total_load,num_feds)
    price.publish(current_price)
    cprice.append(current_price)
    current_time=market_maker.request_next_step()
    
h.helicsFederateDisconnect(market_maker)


low_fed_cost:float=1000000000000.0
low_fed=None
for fed in feds:
    fed.totalCost=float(sum(fed.hourCost))
    if fed.totalCost<low_fed_cost:
        low_fed=fed
        low_fed_cost=fed.totalCost
    print(f"fed {fed.name}:total Cost=${fed.totalCost} total consumption={sum(fed.consume)}")

if low_fed is not None:
    print (f"the winner is Fed {low_fed.name} total cost=${low_fed_cost}")
if args.autobroker:
    h.helicsBrokerDisconnect(broker)

time= list(range(24))

# Initialise the subplot function using number of rows and columns
figure, axis = plt.subplots(1, 2)

# For demand
axis[0].plot(time,loads,color='g',label='load')
axis[0].set_title("Demand profile")

# For price
axis[1].plot(time, cprice)
axis[1].set_title("prices")

# Combine all the operations and display
if not args.no_plot:
    plt.show()
