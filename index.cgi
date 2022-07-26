#!/usr/bin/perl -w

use strict;
use CGI;
use DateTime;

my $cgi = CGI->new;

# there should only be one parameter, the numerical index into the test database
my $subject = $cgi->param('subject') || 1;

### HEADER
print $cgi->header();
print "<html>\n<head><title>HD Hack</title></head>\n<body>\n";
print "<h1>HD Hack</h1>";
print "<p>A very simple, dirty, linear attempt to generate a Human Design reading.</p>";
print "<ol><li>Select a database test subject</li>";
print "<li>Calculate their Design chart date</li>";
print "<li>Use Astrodienst swetest to calculate their personality and design charts</li>";
print "<li>Convert from Astrology to I Ching</li>";
print "<li>Convert from I Ching to Human Design</li>";
print "<li>Offer Interpretations</li>";
print "</ol>";

### 1. Select Database Test Subject
my ( $subject_name, $person_dob, $person_tob, $person_tzob );
print "<hr><h2>Select a test subject</h2>";
print "<form type=get><select name=subject>";
open DB, "< test-database";
my $l = 1;
while (<DB>) {
    chomp;
    my ( $n,$dob,$tob,$tzob ) = split(/\t/,$_);
    next unless defined($n);
    my $selected = "";
    if ( $subject == $l ) {
	$selected = " SELECTED";
	( $subject_name,$person_dob,$person_tob,$person_tzob ) = ( $n,$dob,$tob,$tzob );
    }
    print "<option value=$l$selected>$n</option>";
    $l++;
}
close DB;
print "<input type=submit>";
print "</option></form>";

### 2. Calculate Design Chart Date
print "<hr><h2>Calculate Design Chart Date</h2>";

my $person_datetime = join(" ",$person_dob,$person_tob);
die "Database corrupt" unless $person_datetime =~ m|^\d\d-\d\d-\d\d\d\d \d\d:\d\d$|;

print "<p>Find the angle of the sun at our subjects birth - $person_datetime UT$person_tzob</p>";

my $person_DT = DateTime->new(
    year => $3,month => $2, day => $1,
    hour => $4, minute => $5, second => 0,
    time_zone => "UTC" ) if $person_datetime =~ m|^(\d\d)-(\d\d)-(\d\d\d\d) (\d\d):(\d\d)$|;
$person_DT->subtract( hours => $person_tzob ); # Adjust for time zone

# First find the angle of the Sun
my @swetest_sun = execute_swetest("-p0","-fTL",
                          "-b".$person_DT->dmy("."),
                          "-ut".$person_DT->hms(":"));

my $sun_data = pop @swetest_sun;
my ($sun_degrees,$sun_mins,$sun_secs) = ($1,$2,$3)
    if $sun_data =~ m|UT +(\d+)\xb0 ?([0-9]+)\' ?([0-9.]+)|;
print "<p>Sun found at $sun_degrees\xb0$sun_mins\'$sun_secs.</p>";

$sun_degrees -= 88; $sun_degrees += 360 if $sun_degrees < 0;
print "<p>Now find when the Sun was at $sun_degrees\xb0$sun_mins\'$sun_secs. First search by minutes.</p>";

# Start with a rough guess of Design date - go back 93 days
my $design_guess_DT = $person_DT->clone->subtract( days => 93 );

my @swetest_88_minutes = execute_swetest("-p0","-fTL","-n8640","-s0.00069444444",
					 "-b".$design_guess_DT->dmy("."),
					 "-ut".$design_guess_DT->hms(":"));

my @swetest_88_minutes_grep = grep m|$sun_degrees\xb0 ?$sun_mins|, @swetest_88_minutes;

# Find the First Minute At Design Degree/Minutes (fmadd)
my $fmadd_datetime = shift @swetest_88_minutes_grep; chomp $fmadd_datetime;

print "<pre>$fmadd_datetime  # Found first minute at Sun target degrees/minutes</pre>";

$fmadd_datetime =~ s/ UT.+$//;

my $fmadd_DT = DateTime->new(
    year => $3,month => $2, day => $1,
    hour => $4, minute => $5, second => 0,
    time_zone => "UTC" ) if
    $fmadd_datetime =~ m|^(\d\d)\.(\d\d)\.(\d\d\d\d) (\d\d?):(\d\d)|;
$fmadd_DT->subtract( minutes => 1 );

print "<p>Now search second by second</p>";

my @swetest_88_seconds = execute_swetest("-p0","-fTL","-n3000","-s0.000011574",
                                 "-b".$fmadd_DT->dmy("."),
                                 "-ut".$fmadd_DT->hms(":"));
my $sun_sec1 = $1 if $sun_secs =~ m|(\d+\.\d)|;

my @swetest_88_seconds_grep = grep m|$sun_degrees\xb0 ?$sun_mins\' ?$sun_sec1|, @swetest_88_seconds;

# Find the First Second At Design Degree/Minutes/Seconds (fmaddms)
my $fmaddms_datetime = shift @swetest_88_seconds_grep; chomp $fmaddms_datetime;

print "<pre>$fmaddms_datetime  # Found first second at Sun target degrees/minutes/seconds</pre>";

my $design_DT = DateTime->new(
    year => $3,month => $2, day => $1,
    hour => $4, minute => $5, second => $6,
    time_zone => "UTC" ) if
    $fmaddms_datetime =~ m|^(\d\d)\.(\d\d)\.(\d\d\d\d) (\d\d?):(\d\d):(\d\d)|;

my $design_date = $design_DT->dmy("-");
my $design_time = $design_DT->hms(":");

print "<table>";
print "<tr><td colspan=2><b><u>Personality Chart</u></b></td><td>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;->&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<td colspan=2><u><b>Design Chart</b></u></td></tr>";
print "<tr><td><b>DoB:</b></td><td>$person_dob</td><td></td><td><b>Date:</td><td>$design_date</td></tr>";
print "<tr><td><b>ToB:</b></td><td>$person_tob</td><td></td><td><b>Time:</td><td>$design_time</td></tr>";
print "<tr><td><b>TZoB:</b></td><td>$person_tzob</td><td></td><td></td></tr>";
print "</table>";

print "<hr><h2>Run Astrodienst swetest to get Personality and Design Charts</h2>";
my $person_swetest = join(" ","swetest",
			  "-b".$person_DT->dmy("."),
			  "-ut".$person_DT->hms(":"),
			  "-p0t123456789D -fPZ");
open SWETEST1,"( cd astrodienst ; ./$person_swetest ) |";
my @swetest1 = <SWETEST1>; 
close SWETEST1;
print "<pre>&gt; ".join("",@swetest1)."</pre>";

my $design_swetest = join(" ","swetest",
			  "-b".$design_DT->dmy("."),
			  "-ut".$design_DT->hms(":"),
			  "-p0t123456789D -fPZ");
open SWETEST2,"( cd astrodienst ; ./$design_swetest ) |";
my @swetest2 = <SWETEST2>; 
close SWETEST2;
print "<pre>&gt; ".join("",@swetest2)."</pre>";



print "</body></html>";


exit;

sub execute_swetest {
    my @swetest_params = @_;
    
    my $swetest_cli = join(" ","swetest","-eswe",@swetest_params);
    open SWETEST,"( cd astrodienst ; ./$swetest_cli ) |";
    my @swetest_output = <SWETEST>;
    close SWETEST;
    my $ol = scalar(@swetest_output)-1; $ol = 10 if $ol > 30;
    print "<pre>&gt; ".join("",@swetest_output[0..$ol]);
    print " . . . . . . truncated . . . . . ." if $ol < scalar(@swetest_output)-1;
    print "</pre>";
    return @swetest_output;
}


