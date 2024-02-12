import os
import antspymm
import pandas as pd
import glob as glob
rdir = "/mnt/cluster/data/ANTPD/" 
bd = rdir + "antpd_antspymm/"
dffns=glob.glob( rdir + "studycsvs/*csv" )
mydf = pd.DataFrame()
for f in dffns:
    mydf = pd.concat( [ mydf, pd.read_csv( f ) ] )

# fix for an issue with type
mydf['imageID']='000'
print( mydf.shape )
zz=antspymm.aggregate_antspymm_results_sdf( mydf, subject_col='subjectID', date_col='date', image_col='imageID',  base_path=bd,
splitsep='_', idsep='_', wild_card_modality_id=True, verbose=True)
print( zz.shape )


zz.to_csv( "antpd_antspymm.csv" )

