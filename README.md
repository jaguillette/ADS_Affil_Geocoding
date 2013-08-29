ADS_Affil_Geocoding
===================

This is a python script for taking a set of bibcodes from the Astrophysics Data System and returning a list of geocoded affiliations, with added output for tracking errors

How to use this script:

Create a csv file with the bibcodes that you want geocoded in a single column, making sure that there are no extraneous characters.

Run the script in the terminal from the location of your bibcode csv.

Once it’s completed, there will be a folder with the same name as the csv of bibcodes that you made. In it, you will find a bibcode folder and a few csv files. 
- The bibcodes folder contains individual csv files for each bibcode searched, with the geocoded affiliation data for each.
- Geo_affil_set contains the successful geocoordinate data for the whole set, with per paper counts for each bibcode, but they aren’t de-duped yet. Column descriptions follow:
  - Bibcode is the bibcode for this affiliation.
  - Location is the string from the ADS that was used to find the geocoordinate information.
  - Lat and long are the latitude and longitude given by the Google geocoding API. 
  - The Address is the formatted address returned by the Google geocoding API. This tends to be more standardized than the Location.
  - Country is the country returned by the geocoding API
  - State corresponds to administrative_area_level_1 from the Google geocoding API, defined as “a first-order civil entity below the country level. Within the United States, these administrative levels are states. Not all nations exhibit these administrative levels.”
  - Trusted is a boolean variable, which indicates whether or not the address is likely to be complete, based on whether or not the geocoding API returned a street for the address.
  - Count refers to the number of authors for that bibcode who were affiliated with that Location.
- noAffil contains a list of bibcodes for which there are no recorded affiliations.
- noBib contains a list of bibcodes which the ADS API didn’t return any results for. This happens occasionally and I’m not 100% sure why
- geoErrors contains a list of locations with bibcodes and counts for which the geocoding API didn’t return any results. It includes the error returned by the geocoding API, which should always be ZERO_RESULTS, but which might start indicating that you’re over the request limit if you’ve requested over 2000 geocodings that day, as well as the timestamp for when the request bounced (mostly useful on the off chance that you’re getting bounced for sending too many requests.)

The geocodes csv may contain incorrect locations, and the total counts will still need to be de-duped for affiliation. This should be fixed in later versions.
