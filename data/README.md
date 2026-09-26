# Cultural LFM-1b subset

This dataset is based on the LFM-1b dataset, however, adds acoustic features describing the tracks to the original dataset. 

This new dataset contains
* 55,190 users
* 3,471,884 tracks including acoustic features
* 351,469,333 listening events of those users for tracks we have obtained acoustic features for
* Hofstede's cultural dimensions for 47 countries
* World Happiness Report (WHR) data for 164 countries

## Creation
For the creation of the dataset, we extract all users for which the original dataset contains country information for. We extract the listening events of these users and match the tracks against the Spotify API to subsequently retrieve the acoustic features of these tracks (cf. [Spotify Audio Feature Description](https://developer.spotify.com/documentation/web-api/reference/object-model/#audio-features-object)). The final dataset contains only events of users with country information and tracks with acoustic features.

## Files
All files are tab-separated, with no quoting of strings. The dataset contains the following files, whose content we describe in more detail in the following parts.

* acoustic_features_lfm_id.tsv: acoustic features for all tracks in the dataset, identified by their LFM track identifier
* events.tsv: listening events for all users
* hofstede.tsv: Hofstede's cultural dimensions
* users.tsv: user metadata
* world_happiness_report_2018.tsv: World Happiness Report data

## acoustic_features_lfm_id.tsv
This file contains the following columns (cf. [Spotify Audio Feature Description](https://developer.spotify.com/documentation/web-api/reference/object-model/#audio-features-object) for further description of acoustic features):
* track_id: LFM-1b's id for the track (int)
* danceability: how suitable the track is for dancing (float, [0,1])
* energy: perceptual measure of intensity and activity (float, [0,1])
* key: key of the track (int, pitch class notation)
* loudness: loudness in decibels (float)
* mode: major (1) or minor (0) (int)
* speechiness: presence of spoken words (float, [0,1])
* acousticness: confidence whether track is acoustic (float, [0,1])
* instrumentalness: likelihood that track contains no vocals (float, [0,1])
* liveness: presence of an audience in recording (float, [0,1])
* valence: musical positiveness conveyed (float, [0,1]) 
* tempo: tempo of track in beats per minute (float)
Please note that the features for a single track may not be complete as the full information was not provided by Spotify's API.

## events.tsv
This file contains the following information regarding listening events, simply filtered from LFM-1b's original file:
* user_id: LFM-1b's user id (int)
* artist_id: LFM-1b's artist id (int)
* album_id: LFM-1b's album id (int)
* track_id: LFM-1b's track id (int)
* timestamp: timestamp of event (int, unix time)

## hofstede.tsv
Hofstede's cultural dimensions contain the following data (cf. [Hofstede's Cultural Dimensions](https://geerthofstede.com/culture-geert-hofstede-gert-jan-hofstede/6d-model-of-national-culture/)). This data is freely made available by Hofstede et al. at [Base Culture Data for Six Dimensions (Dimension Data Matrix)](https://geerthofstede.com/research-and-vsm/dimension-data-matrix/):
* no: id for entry (int)
* ctr: abbreviated country name (string)
* country: country name (string)
* power_distance: extent to which the less powerful members of organizations and institutions accept and expect that power is distributed unqually (int)
* individualism: extent to which people feel independent (int)
* masculinity: extent to which the use of force is endorsed socially (int)
* uncertainty_avoidance: society's tolerance for uncertainty and ambiguity (int)
* long_term_orientation: associates the connection of the past with the current and future actions/challenges (int)
* indulgence: good things in life, measures happiness to some extent (int)

## users.tsv
Contains the filtered user information from the original LFM-1b dataset:
* user_id: LFM-1b's user id (int)
* country: country information (String)
* age: age of the user (int)
* gender: m or f (char)
* playcount: total number of listened tracks; note that this is not consistent with this dataset as we remove tracks were not able to obtain acoustic features for (int)
* registered_unixtime: timestamp of registration (int, unix time)

## world_happiness_report_2018.tsv
Contains the data of the world happiness report 2018 (cf. [World Happiness Report 2018](http://worldhappiness.report/ed/2018/)):
* country: country name (String)
* year: year of data collection
* Life Ladder: Happiness score or subjective well-being, average self-assessment  (float)
* Log GDP per capita: Logarithm of purchasing power parity (float)
* Social support: having someone to count on in time of trouble (float, [0,1])
* Healthy life expectancy at birth: length of healthy life (float)
* Freedom to make life choices: satisfaction with freedom to choose what to do with own's life (float, [0,1])
* Generosity: average of answers to question whether money was donated to charity in the last month (float, [0,1])
* Perceptions of corruption: average of answers to questions regarding spread of corruption in government and businesses (float, [0,1])
* Positive affect: average of measurements regarding happiness, laugh and enjoyment (float, [0,1]
* Negative affect: average of measurements regarding worry, sadness and anger (float, [0,1])
* Confidence in national government: 
* Democratic Quality: Quality of democracy: standardized indicators for governments accountability, political stability, freedom of speech (float)
* Delivery Quality: Implementation of democracy: standardized indicators for efficiency of government, quality of regulation, rule of law, fight against corruption (float)
* Standard deviation of ladder by country-year: standard deviation of variable life ladder (float)
* Standard deviation/Mean of ladder by country-year: 
* GINI index (World Bank estimate): Gini index as estimated by World Bank (float)
* GINI index (World Bank estimate), average 2000-15: Gini index as estimated by World bank (average across 2000-2015)
* gini of household income reported in Gallup, by wp5-year: Gini-index of household income extracted from Gallup report

More information  on variables can be found in [Appendix](https://s3.amazonaws.com/happiness-report/2016/StatisticalAppendixWHR2016.pdf).
