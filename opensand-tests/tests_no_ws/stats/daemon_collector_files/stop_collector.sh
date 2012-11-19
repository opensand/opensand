#!/bin/sh

stop_collector() {
	PID=`cat /tmp/sand_collector_pid`
	echo "Stopping collector (PID $PID)" | tee -a /tmp/test_sand_collector.log
	kill -TERM "$PID"
	rm /tmp/sand_collector_pid
	rm -r /tmp/tmp*_opensand_collector
}

check_file_lines() {
	expected_lnum=$1
	name=$2

	if [ ! -f $name ]; then
		echo "$name log file does not exist!"  | tee -a /tmp/test_sand_collector.log
		stop_collector
		exit 1
	fi

	lnum= `wc -l < $name`
	if [ $lnum -ne $expected_lnum ]; then
		echo "$name log file has $lnum lines, expected $expected_lnum." | tee -a /tmp/test_sand_collector.log
		stop_collector
		exit 1
	fi
}

check_file_data() {
	expected_data=$1
	name=$2

	if [ ! -f $name ]; then
		echo "$name log file does not exist!"  | tee -a /tmp/test_sand_collector.log
		stop_collector
		exit 1
	fi

	file_data=`cut -d " " -f 2- $name | tr "\n" "|"`

	if [ "$file_data" != "$expected_data" ]; then
		echo "$name log file has incorrect log data '$file_data'." | tee -a /tmp/test_sand_collector.log
		stop_collector
		exit 1
	fi
}

cd /tmp/tmp*opensand_collector/st1/test_prog/ || (echo "Failed to cd to the test_prog log dir" | tee -a /tmp/test_sand_collector.log ;stop_collector ; exit 1)

echo /tmp/tmp*_opensand_collector/st1/test_prog/ | tee -a /tmp/test_sand_collector.log
pwd | tee -a /tmp/test_sand_collector.log
ls -l | tee -a /tmp/test_sand_collector.log

check_file_lines 0 double_probe.log
check_file_data "info_event Hello, World.|info_event Hello, World.|" event_log.txt
check_file_data "10.0|45.7999992371|224.800003052|1119.80004883|5594.80029297|27969.8007812|139844.796875|699219.8125|3496094.75|17480470.0|87402344.0|437011712.0|2185058560.0|10925292544.0|54626463744.0|273132322816.0|1.36566158131e+12|6.82830803763e+12|3.41415401882e+13|1.70707703038e+14|" float_probe.log
check_file_lines 0 int32_avg_probe.log
check_file_lines 0 int32_dis_probe.log
check_file_data "42|43|44|45|46|47|48|49|50|51|52|53|54|55|56|57|58|59|60|61|" int32_last_probe.log
check_file_lines 0 int32_max_probe.log
check_file_lines 0 int32_min_probe.log
check_file_lines 0 int32_sum_probe.log

stop_collector
exit 0
