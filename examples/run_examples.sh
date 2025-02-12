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
echo "##################################################################"
echo "##################################################################"
echo "Running CFG: $CFG in --minitest mode"
submg-cli submit \
--config $LOCAL \
--staging-dir $STAGING_DIR \
--logging-dir $LOGGING_DIR \
--submit-samples \
--submit-reads \
--submit-assembly \
--submit-bins \
--submit-mags \
--minitest
rm -rf $STAGING_DIR $LOGGING_DIR

CFG=01_samples_reads_assembly_bins_mags.yaml
RANDOM_STR=$(tr -dc 'A-Za-z0-9' </dev/urandom | head -c 5)
cp $CFG $LOCAL
sed -i "s/idx00/${RANDOM_STR}/g" "$LOCAL"
echo ""
echo "##################################################################"
echo "##################################################################"
echo "Running CFG: $CFG"
submg-cli submit \
--config $LOCAL \
--staging-dir $STAGING_DIR \
--logging-dir $LOGGING_DIR \
--submit-samples \
--submit-reads \
--submit-assembly \
--submit-bins \
--submit-mags
rm -rf $STAGING_DIR $LOGGING_DIR

CFG=02_samples_reads_assembly_bins.yaml
RANDOM_STR=$(tr -dc 'A-Za-z0-9' </dev/urandom | head -c 5)
cp $CFG $LOCAL
sed -i "s/idx00/${RANDOM_STR}/g" "$LOCAL"
echo ""
echo "##################################################################"
echo "##################################################################"
echo "Running CFG: $CFG"
submg-cli submit \
--config $LOCAL \
--staging-dir $STAGING_DIR \
--logging-dir $LOGGING_DIR \
--submit-samples \
--submit-reads \
--submit-assembly \
--submit-bins
rm -rf $STAGING_DIR $LOGGING_DIR

CFG=03_samples_reads_assembly.yaml
RANDOM_STR=$(tr -dc 'A-Za-z0-9' </dev/urandom | head -c 5)
cp $CFG $LOCAL
sed -i "s/idx00/${RANDOM_STR}/g" "$LOCAL"
echo ""
echo "##################################################################"
echo "##################################################################"
echo "Running CFG: $CFG"
submg-cli submit \
--config $LOCAL \
--staging-dir $STAGING_DIR \
--logging-dir $LOGGING_DIR \
--submit-samples \
--submit-reads \
--submit-assembly
rm -rf $STAGING_DIR $LOGGING_DIR

CFG=04_reads_assembly_bins_mags.yaml
RANDOM_STR=$(tr -dc 'A-Za-z0-9' </dev/urandom | head -c 5)
cp $CFG $LOCAL
sed -i "s/idx00/${RANDOM_STR}/g" "$LOCAL"
echo ""
echo "##################################################################"
echo "##################################################################"
echo "Running CFG: $CFG"
submg-cli submit \
--config $LOCAL \
--staging-dir $STAGING_DIR \
--logging-dir $LOGGING_DIR \
--submit-reads \
--submit-assembly \
--submit-bins \
--submit-mags
rm -rf $STAGING_DIR $LOGGING_DIR

CFG=05_reads_assembly_bins.yaml
RANDOM_STR=$(tr -dc 'A-Za-z0-9' </dev/urandom | head -c 5)
cp $CFG $LOCAL
sed -i "s/idx00/${RANDOM_STR}/g" "$LOCAL"
echo ""
echo "##################################################################"
echo "##################################################################"
echo "Running CFG: $CFG"
submg-cli submit \
--config $LOCAL \
--staging-dir $STAGING_DIR \
--logging-dir $LOGGING_DIR \
--submit-reads \
--submit-assembly \
--submit-bins
rm -rf $STAGING_DIR $LOGGING_DIR

CFG=06_reads_assembly.yaml
RANDOM_STR=$(tr -dc 'A-Za-z0-9' </dev/urandom | head -c 5)
cp $CFG $LOCAL
sed -i "s/idx00/${RANDOM_STR}/g" "$LOCAL"
echo ""
echo "##################################################################"
echo "##################################################################"
echo "Running CFG: $CFG"
submg-cli submit \
--config $LOCAL \
--staging-dir $STAGING_DIR \
--logging-dir $LOGGING_DIR \
--submit-reads \
--submit-assembly
rm -rf $STAGING_DIR $LOGGING_DIR

CFG=07_assembly_bins_mags.yaml
RANDOM_STR=$(tr -dc 'A-Za-z0-9' </dev/urandom | head -c 5)
cp $CFG $LOCAL
sed -i "s/idx00/${RANDOM_STR}/g" "$LOCAL"
echo ""
echo "##################################################################"
echo "##################################################################"
echo "Running CFG: $CFG"
submg-cli submit \
--config $LOCAL \
--staging-dir $STAGING_DIR \
--logging-dir $LOGGING_DIR \
--submit-assembly \
--submit-bins \
--submit-mags
rm -rf $STAGING_DIR $LOGGING_DIR

CFG=08_assembly_bins.yaml
RANDOM_STR=$(tr -dc 'A-Za-z0-9' </dev/urandom | head -c 5)
cp $CFG $LOCAL
sed -i "s/idx00/${RANDOM_STR}/g" "$LOCAL"
echo ""
echo "##################################################################"
echo "##################################################################"
echo "Running CFG: $CFG"
submg-cli submit \
--config $LOCAL \
--staging-dir $STAGING_DIR \
--logging-dir $LOGGING_DIR \
--submit-assembly \
--submit-bins
rm -rf $STAGING_DIR $LOGGING_DIR

CFG=09_assembly.yaml
RANDOM_STR=$(tr -dc 'A-Za-z0-9' </dev/urandom | head -c 5)
cp $CFG $LOCAL
sed -i "s/idx00/${RANDOM_STR}/g" "$LOCAL"
echo ""
echo "##################################################################"
echo "##################################################################"
echo "Running CFG: $CFG"
submg-cli submit \
--config $LOCAL \
--staging-dir $STAGING_DIR \
--logging-dir $LOGGING_DIR \
--submit-assembly
rm -rf $STAGING_DIR $LOGGING_DIR

CFG=10_bins_mags.yaml
RANDOM_STR=$(tr -dc 'A-Za-z0-9' </dev/urandom | head -c 5)
cp $CFG $LOCAL
sed -i "s/idx00/${RANDOM_STR}/g" "$LOCAL"
echo ""
echo "##################################################################"
echo "##################################################################"
echo "Running CFG: $CFG"
submg-cli submit \
--config $LOCAL \
--staging-dir $STAGING_DIR \
--logging-dir $LOGGING_DIR \
--submit-bins \
--submit-mags
rm -rf $STAGING_DIR $LOGGING_DIR

CFG=11_bins.yaml
RANDOM_STR=$(tr -dc 'A-Za-z0-9' </dev/urandom | head -c 5)
cp $CFG $LOCAL
sed -i "s/idx00/${RANDOM_STR}/g" "$LOCAL"
echo ""
echo "##################################################################"
echo "##################################################################"
echo "Running CFG: $CFG"
submg-cli submit \
--config $LOCAL \
--staging-dir $STAGING_DIR \
--logging-dir $LOGGING_DIR \
--submit-bins
rm -rf $STAGING_DIR $LOGGING_DIR

CFG=12_mags.yaml
RANDOM_STR=$(tr -dc 'A-Za-z0-9' </dev/urandom | head -c 5)
cp $CFG $LOCAL
sed -i "s/idx00/${RANDOM_STR}/g" "$LOCAL"
echo ""
echo "##################################################################"
echo "##################################################################"
echo "Running CFG: $CFG"
submg-cli submit \
--config $LOCAL \
--staging-dir $STAGING_DIR \
--logging-dir $LOGGING_DIR \
--submit-mags
rm -rf $STAGING_DIR $LOGGING_DIR

echo ""
echo "##################################################################"
echo "##################################################################"
echo "All examples submitted"
echo "##################################################################"
echo "##################################################################"

CFG=13_samples.yaml
RANDOM_STR=$(tr -dc 'A-Za-z0-9' </dev/urandom | head -c 5)
cp $CFG $LOCAL
sed -i "s/idx00/${RANDOM_STR}/g" "$LOCAL"
echo ""
echo "##################################################################"
echo "##################################################################"
echo "Running CFG: $CFG"
submg-cli submit \
--config $LOCAL \
--staging-dir $STAGING_DIR \
--logging-dir $LOGGING_DIR \
--submit-samples
rm -rf $STAGING_DIR $LOGGING_DIR

CFG=14_reads.yaml
RANDOM_STR=$(tr -dc 'A-Za-z0-9' </dev/urandom | head -c 5)
cp $CFG $LOCAL
sed -i "s/idx00/${RANDOM_STR}/g" "$LOCAL"
echo ""
echo "##################################################################"
echo "##################################################################"
echo "Running CFG: $CFG"
submg-cli submit \
--config $LOCAL \
--staging-dir $STAGING_DIR \
--logging-dir $LOGGING_DIR \
--submit-reads
rm -rf $STAGING_DIR $LOGGING_DIR

CFG=15_samples_reads.yaml
RANDOM_STR=$(tr -dc 'A-Za-z0-9' </dev/urandom | head -c 5)
cp $CFG $LOCAL
sed -i "s/idx00/${RANDOM_STR}/g" "$LOCAL"
echo ""
echo "##################################################################"
echo "##################################################################"
echo "Running CFG: $CFG"
submg-cli submit \
--config $LOCAL \
--staging-dir $STAGING_DIR \
--logging-dir $LOGGING_DIR \
--submit-samples \
--submit-reads
rm -rf $STAGING_DIR $LOGGING_DIR

echo ""
echo "##################################################################"
echo "##################################################################"
echo "All examples submitted"
echo "##################################################################"
echo "##################################################################"