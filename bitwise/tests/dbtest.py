"""For Pico and ESP32 """

try:
    from gc import mem_free, collect
    mem_free_present = True
    mem_start = mem_free()

except:
    mem_free_present = False

import os,sys



print('Before fsinit')
print('getcwd ', os.getcwd())
print('path   ',sys.path)
try:
    import fsinit
except:
    import tests.fsinit as fsinit
del(fsinit)

print('After fsinit')
print('getcwd ', os.getcwd())
print('path   ',sys.path)

# os.chdir('tests')
# print('getcwd ', os.getcwd())

# import lib.vdict
    

from rpzc_demo import RPZeroClub

rpzc = RPZeroClub()

rpzc.load_all()


if mem_free_present:

    print('After load all')
    print('Total memory started:  ', mem_start )
    print('Mem used:              ',  mem_start-mem_free())
    
    collect()
    
    print('Mem used after collect: ',  mem_start-mem_free())
    print()
    ### About 60K on RPPico ?  has machine class not in ESP32 locals. Also rp2.
    ### Says 132K for ESP32 ?  There's a bdev Partition entry not on Pico.  Also os.

# mtups, ptups, rtups, pmtups, rtups, prtups, etups 
    
mtups = list(rpzc.Member.dump(resolve_types=True))
ptups = list(rpzc.Project.dump(resolve_types=True))
rtups = list(rpzc.Role.dump(resolve_types=True))
pmtups = list(rpzc.ProjectMember.dump(resolve_types=True))
rtups = list(rpzc.Role.dump(resolve_types=True))
prtups = list(rpzc.ProjectResource.dump(resolve_types=True))
etups = list(rpzc.Event.dump(resolve_types=True))

if mem_free_present:

    print('After create tups')
    print('Total memory started:  ', mem_start )
    print('Mem used:              ',  mem_start-mem_free())
    collect()
    print('Mem used after collect: ',  mem_start-mem_free())
    print()

del(rpzc)
del(RPZeroClub)
 
if mem_free_present:

    print('After del rpzc db')

    print('Total memory started:  ', mem_start )
    print('Mem used:              ',  mem_start-mem_free())
    
    collect()
    
    print('Mem used after collect: ',  mem_start-mem_free())
    ### About 60K on RPPico ?  has machine class not in ESP32 locals. Also rp2.
    ### Says 132K for ESP32 ?  There's a bdev Partition entry not on Pico.  Also os.


    print()
    print('locals() ', locals())
    print()
    if 'bdev' in locals():
        print('ESP32 -> dir(bdev) ', dir(bdev))
        print('bdev.info()  ', bdev.info())



