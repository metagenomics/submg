set -e

LOCAL=localtest.yaml
STAGING_DIR=localtest/staging
LOGGING_DIR=localtest/logging
rm -rf $STAGING_DIR $LOGGING_DIR


CFG=01_samples_reads_assembly_bins_mags.yaml
RANDOM_STR=$(tr -dc 'A-Za-z0-9' </dev/urandom | head -c 5)
cp $CFG $LOCAL
sed -i "s/idx00/${RANDOM_STR}/g" "$LOCAL"
echo ""
echo "######################"
echo "######################"
echo "Running CFG: $CFG"
synum submit \
--config $LOCAL \
--staging_dir $STAGING_DIR \
--logging_dir $LOGGING_DIR \
--submit_samples \
--submit_reads \
--submit_assembly \
--submit_bins \
--submit_mags
rm -rf $STAGING_DIR $LOGGING_DIR

CFG=02_samples_reads_assembly_bins.yaml
RANDOM_STR=$(tr -dc 'A-Za-z0-9' </dev/urandom | head -c 5)
cp $CFG $LOCAL
sed -i "s/idx00/${RANDOM_STR}/g" "$LOCAL"
echo ""
echo "######################"
echo "######################"
echo "Running CFG: $CFG"
synum submit \
--config $LOCAL \
--staging_dir $STAGING_DIR \
--logging_dir $LOGGING_DIR \
--submit_samples \
--submit_reads \
--submit_assembly \
--submit_bins
rm -rf $STAGING_DIR $LOGGING_DIR

CFG=03_samples_reads_assembly.yaml
RANDOM_STR=$(tr -dc 'A-Za-z0-9' </dev/urandom | head -c 5)
cp $CFG $LOCAL
sed -i "s/idx00/${RANDOM_STR}/g" "$LOCAL"
echo ""
echo "######################"
echo "######################"
echo "Running CFG: $CFG"
synum submit \
--config $LOCAL \
--staging_dir $STAGING_DIR \
--logging_dir $LOGGING_DIR \
--submit_samples \
--submit_reads \
--submit_assembly
rm -rf $STAGING_DIR $LOGGING_DIR

CFG=04_reads_assembly_bins_mags.yaml
RANDOM_STR=$(tr -dc 'A-Za-z0-9' </dev/urandom | head -c 5)
cp $CFG $LOCAL
sed -i "s/idx00/${RANDOM_STR}/g" "$LOCAL"
echo ""
echo "######################"
echo "######################"
echo "Running CFG: $CFG"
synum submit \
--config $LOCAL \
--staging_dir $STAGING_DIR \
--logging_dir $LOGGING_DIR \
--submit_reads \
--submit_assembly \
--submit_bins \
--submit_mags
rm -rf $STAGING_DIR $LOGGING_DIR

CFG=05_reads_assembly_bins.yaml
RANDOM_STR=$(tr -dc 'A-Za-z0-9' </dev/urandom | head -c 5)
cp $CFG $LOCAL
sed -i "s/idx00/${RANDOM_STR}/g" "$LOCAL"
echo ""
echo "######################"
echo "######################"
echo "Running CFG: $CFG"
synum submit \
--config $LOCAL \
--staging_dir $STAGING_DIR \
--logging_dir $LOGGING_DIR \
--submit_reads \
--submit_assembly \
--submit_bins
rm -rf $STAGING_DIR $LOGGING_DIR

CFG=06_reads_assembly.yaml
RANDOM_STR=$(tr -dc 'A-Za-z0-9' </dev/urandom | head -c 5)
cp $CFG $LOCAL
sed -i "s/idx00/${RANDOM_STR}/g" "$LOCAL"
echo ""
echo "######################"
echo "######################"
echo "Running CFG: $CFG"
synum submit \
--config $LOCAL \
--staging_dir $STAGING_DIR \
--logging_dir $LOGGING_DIR \
--submit_reads \
--submit_assembly
rm -rf $STAGING_DIR $LOGGING_DIR

CFG=07_assembly_bins_mags.yaml
RANDOM_STR=$(tr -dc 'A-Za-z0-9' </dev/urandom | head -c 5)
cp $CFG $LOCAL
sed -i "s/idx00/${RANDOM_STR}/g" "$LOCAL"
echo ""
echo "######################"
echo "######################"
echo "Running CFG: $CFG"
synum submit \
--config $LOCAL \
--staging_dir $STAGING_DIR \
--logging_dir $LOGGING_DIR \
--submit_assembly \
--submit_bins \
--submit_mags
rm -rf $STAGING_DIR $LOGGING_DIR

CFG=08_assembly_bins.yaml
RANDOM_STR=$(tr -dc 'A-Za-z0-9' </dev/urandom | head -c 5)
cp $CFG $LOCAL
sed -i "s/idx00/${RANDOM_STR}/g" "$LOCAL"
echo ""
echo "######################"
echo "######################"
echo "Running CFG: $CFG"
synum submit \
--config $LOCAL \
--staging_dir $STAGING_DIR \
--logging_dir $LOGGING_DIR \
--submit_assembly \
--submit_bins
rm -rf $STAGING_DIR $LOGGING_DIR

CFG=09_assembly.yaml
RANDOM_STR=$(tr -dc 'A-Za-z0-9' </dev/urandom | head -c 5)
cp $CFG $LOCAL
sed -i "s/idx00/${RANDOM_STR}/g" "$LOCAL"
echo ""
echo "######################"
echo "######################"
echo "Running CFG: $CFG"
synum submit \
--config $LOCAL \
--staging_dir $STAGING_DIR \
--logging_dir $LOGGING_DIR \
--submit_assembly
rm -rf $STAGING_DIR $LOGGING_DIR

CFG=10_bins_mags.yaml
RANDOM_STR=$(tr -dc 'A-Za-z0-9' </dev/urandom | head -c 5)
cp $CFG $LOCAL
sed -i "s/idx00/${RANDOM_STR}/g" "$LOCAL"
echo ""
echo "######################"
echo "######################"
echo "Running CFG: $CFG"
synum submit \
--config $LOCAL \
--staging_dir $STAGING_DIR \
--logging_dir $LOGGING_DIR \
--submit_bins \
--submit_mags
rm -rf $STAGING_DIR $LOGGING_DIR

CFG=11_bins.yaml
RANDOM_STR=$(tr -dc 'A-Za-z0-9' </dev/urandom | head -c 5)
cp $CFG $LOCAL
sed -i "s/idx00/${RANDOM_STR}/g" "$LOCAL"
echo ""
echo "######################"
echo "######################"
echo "Running CFG: $CFG"
synum submit \
--config $LOCAL \
--staging_dir $STAGING_DIR \
--logging_dir $LOGGING_DIR \
--submit_bins
rm -rf $STAGING_DIR $LOGGING_DIR

CFG=12_mags.yaml
RANDOM_STR=$(tr -dc 'A-Za-z0-9' </dev/urandom | head -c 5)
cp $CFG $LOCAL
sed -i "s/idx00/${RANDOM_STR}/g" "$LOCAL"
echo ""
echo "######################"
echo "######################"
echo "Running CFG: $CFG"
synum submit \
--config $LOCAL \
--staging_dir $STAGING_DIR \
--logging_dir $LOGGING_DIR \
--submit_mags
rm -rf $STAGING_DIR $LOGGING_DIR

echo ""
echo "######################"
echo "######################"
echo "All examples submitted"
echo "######################"
echo "######################"