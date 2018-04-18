import cherrypy
import sqlite3 as sql
import os
import json
from ast import literal_eval
import requests
import math
from statistics import mode

# Update this value before every event
# Use the event codes given by thebluealliance
CURRENT_EVENT = '2018necmp'
DEFAULT_MODE = 'averages'


class ScoutServer(object):
    @cherrypy.expose
    def index(self, m='', e=''):

        # First part is to handle event selection. When the event is changed, a POST request is sent here.
        illegal = ''  # i competely forget what this variable does, just leave it
        if e != '':
            if os.path.isfile('data_' + e + '.db'):
                cherrypy.session['event'] = e
            else:
                illegal = e
        if 'event' not in cherrypy.session:
            cherrypy.session['event'] = CURRENT_EVENT

        if m != '':
            cherrypy.session['mode'] = m
        if 'mode' not in cherrypy.session:
            cherrypy.session['mode'] = DEFAULT_MODE

        # This section generates the table of averages
        table = ''
        conn = sql.connect(self.datapath())
        if (cherrypy.session['mode'] == "averages"):
            data = conn.cursor().execute('SELECT * FROM averages ORDER BY apr DESC').fetchall()
        else:
            data = conn.cursor().execute('SELECT * FROM maxes ORDER BY apr DESC').fetchall()
        conn.close()
        for team in data:  # this table will need to change based on the number of columns on the main page
            table += '''
            <tr>
                <td><a href="team?n={0}">{0}</a></td>
                <td>{1}</td>
                <td>{2}</td>
                <td>{3}</td>
                <td>{4}</td>
                <td>{5}</td>
                <td>{6}</td>
                <td>{7}</td>
            </tr>
            '''.format(team[0],  team[1],team[2], team[3], team[4], team[5] , team[6], team[7],team[8])
        # in this next block, update the event list and the column titles
        return '''
        <html>
            <head>
                <title>PiScout</title>
                <link href="<link href="https://fonts.googleapis.com/css?family=Oxygen" rel="stylesheet" type="text/css">
                <link href="./static/css/style.css" rel="stylesheet">
                <script src="https://ajax.googleapis.com/ajax/libs/jquery/1.11.3/jquery.min.js"></script>
                <script>
                if (typeof jQuery === 'undefined')
                  document.write(unescape('%3Cscript%20src%3D%22/static/js/jquery.js%22%3E%3C/script%3E'));
                </script>
                <script type="text/javascript" src="./static/js/jquery.tablesorter.js"></script>
                <script>
                $(document).ready(function() {{
                    $("table").tablesorter();
                    $("#{1}").attr("selected", "selected");
                    $("#{2}").attr("selected", "selected");
                    console.log($("#{1}").selected);
                    {3}
                }});
                </script>
            </head>
            <body>
            <div style="max-width: 1000px; margin: 0 auto;">
                <br>
                <div style="vertical-align:top; float:left; width: 300px;">
                    <h1>PiScout 2.0</h1>
                    <h2>FRC 2067</h2>
                    <br><br>
                    <p class="main">Search Team</p>
                    <form method="get" action="team">
                        <input class="field" type="text" maxlength="4" name="n" autocomplete="off"/>
                        <button class="submit" type="submit">Submit</button>
                    </form>
                    <br><br>
                    <p class="main">Main Display</p>
                    <form method="post" action="">
                        <select class="fieldsm" name="m">
                            <option id="averages" value="averages">Averages</option>
                            <option id="maxes" value="maxes">Maxes</option>
                        </select>
                        <button class="submit" type="submit">Submit</button>
                    </form>
                    <br><br>
                     <p class="main">Change Event</p>
                    <form method="post" action="">
                        <select class="fieldsm" name="e">
                          <option id="2018water" value="2018water">Waterbury District</option>
                          <option id="2018SE" value = "2018SE">SE CT District</option>
                          <option id="2018cthar" value = "2018cthar">Hartford CT District</option>
                          <option id="2018necmp" value = "2018necmp">District Champs</option>
                        </select>
                        <button class="submit" type="submit">Submit</button>
                    </form>
                    <p class="main">Compare</p>
                    <form method="get" action="compare">
                        <select class="fieldsm" name="t">
                          <option value="team">Teams</option>
                          <option value="alliance">Alliances</option>
                        </select>
                        <button class="submit" type="submit">Submit</button>
                    </form>
                    <br><br>
                    <p class="main">View Matches</p>
                    <form method="get" action="matches">
                        <select class="fieldsm" name="n">
                          <option value="2067">2067 matches</option>
                          <option value="0">All matches</option>
                        </select>
                        <button class="submit" type="submit">Submit</button>
                    </form>
                </div>

                <div style="vertical-align:top; border 1px solid black; overflow: hidden">
                 <table style="font-size: 140%;" class="tablesorter">
                    <thead><tr>
                        <th>Team</th>
                        <th>APR</th>
                        <th>Total</th>
                        <th>Auto Switch</th>
                        <th>Auto Scale</th>
                        <th>Tele Switch</th>
                        <th>Tele Scale</th>
                        <th>Tele Exch</th>
                    </tr></thead>
                    <tbody>{0}</tbody>
                </table>
                </div>
            </div>
            </body>
        </html>'''.format(table, cherrypy.session['event'], cherrypy.session['mode'],
                          '''alert('There is no data for the event "{}"')'''.format(illegal) if illegal else '')

        # Show a detailed summary for a given team
    @cherrypy.expose()
    def team(self, n="2067"):
        if not n.isdigit():
            raise cherrypy.HTTPRedirect('/')
        if int(n) == 666:
            raise cherrypy.HTTPError(403, 'Satan has commanded me to not disclose his evil strategy secrets.')
        conn = sql.connect(self.datapath())
        cursor = conn.cursor()
        entries = cursor.execute('SELECT * FROM scout WHERE d0=? ORDER BY d1 DESC', (n,)).fetchall()
        averages = cursor.execute('SELECT * FROM averages WHERE team=?', (n,)).fetchall()
        assert len(averages) < 2  # ensure there aren't two entries for one team
        if len(averages):
            s = averages[0]
            print(s)
        else:
            s = [0] * 7  # generate zeros if no data exists for the team yet

        comments = cursor.execute('SELECT * FROM comments WHERE team=?', (n,)).fetchall()
        conn.close()

        # Generate html for comments section
        commentstr = ''
        #for comment in comments:
         #   commentstr += '<div class="commentbox"><p>{}</p></div>'.format(comment[1])

        # Iterate through all the data entries and generate some text to go in the main table
        # this entire section will need to change from year to year
        output = ''
        dataset = []
        for e in entries:
            # Important: the index of e refers to the number of the field set in main.py
            # For example e[1] gets value #1 from main.py
            # Important: the index of e refers to the number of the field set in main.py
            # For example e[1] gets value #0 from main.py
            dp = {"match": e[1], "autoswitch":0, "autoscale":0, "teleswitch":0, "telescale":0, "teleexch":0,"teledrop":0}
            a = ''
            a += 'baseline, ' if e[6] else ''
            dp['autoswitch'] += e[2]
            a += str(e[2]) + 'x switch, ' if e[2] else ''
            a += str(e[3]) + 'x scale, ' if e[3] else ''
            a += str(e[4]) + 'x exch, ' if e[4] else ''
            a+=  str(e[5]) + 'x dropped, ' if e[5] else ''
            dp['autoscale'] += e[3]

            d = ''
            d += str(e[7]) + 'x switch, ' if e[7] else ''
            d+= str(e[11]) + 'x opp switch, ' if e[11] else ''
            d += str(e[8]) + 'x scale, ' if e[8] else ''
            d += str(e[9]) + 'x exch, ' if e[9] else ''
            d += str(e[10]) + 'x drop ' if e[10] else ''
            dp['teleswitch'] = e[7]
            dp['telescale'] += e[8]
            dp['teleexch'] += e[9]
            dp["teledrop"]+= e[10]

            end = ''
            end +='climb, ' if e[12] else ''
            end += 'park ' if e[13]  else ''
            end += 'climbed bot ' if e[14] else ''

            o = ''
            o += 'defense, ' if e[15] else ''
            o+= 'defended,' if e[16] else ''
            c = ''
            c += e[17]

            # Generate a row in the table for each match
            output += '''
            <tr {6}>
                <td>{0}</td>
                <td>{1}</td>
                <td>{2}</td>
                <td>{3}</td>
                <td>{4}</td>
                <td>{5}</td>
                <td><a class="flag" href="javascript:flag({6}, {7});">X</a></td>
            </tr>'''.format(e[1], a, d,end, o,c, 'style="color: #B20000"' if e[18] else '', e[1], e[18])
            for key, val in dp.items():
                dp[key] = round(val, 2)
            if not e[18]:  # if flagged
                dataset.append(dp)  # add it to dataset, which is an array of data that is fed into the graphs
        dataset.reverse()  # reverse so that graph is in the correct order

        # Grab the image from the blue alliance
        imcode = ''
        headers = {"X-TBA-App-Id": "frc2067:scouting-system:v01"}
        m = []
        try:
            # get the picture for a given team
            m = self.get("http://www.thebluealliance.com/api/v2/team/frc{0}/media".format(n), params=headers).json()
            if m.status_code == 400:
                m = []
        except:
            pass  # swallow the error lol
        for media in m:
            if media['type'] == 'imgur':  # check if there's an imgur image on TBA
                imcode = '''<br>
                    <div style="text-align: center">
                    <p style="font-size: 32px; line-height: 0em;">Image</p>
                    <img src=http://i.imgur.com/{}.jpg></img>
                    </div>'''.format(media['foreign_key'])
                break
            if media['type'] == 'cdphotothread':
                imcode = '''<br>
                    <div style="text-align: center">
                    <p style="font-size: 32px; line-height: 0em;">Image</p>
                    <img src=http://chiefdelphi.com/media/img/{}></img>
                    </div>'''.format(media['details']['image_partial'].replace('_l', '_m'))
                break

                # Every year, update the labels for the graphs. The data will come from the variable dataset
                # Then update all the column headers and stuff
        return '''
        <html>
            <head>
                <title>{0} | PiScout</title>
                <link href="https://fonts.googleapis.com/css?family=Oxygen" rel="stylesheet" type="text/css">
                <link href="/static/css/style.css" rel="stylesheet">
                <script type="text/javascript" src="/static/js/amcharts.js"></script>
                <script type="text/javascript" src="/static/js/serial.js"></script>
                <script src="https://ajax.googleapis.com/ajax/libs/jquery/1.11.3/jquery.min.js"></script>
                <script>
                if (typeof jQuery === 'undefined')
                  document.write(unescape('%3Cscript%20src%3D%22/static/js/jquery.js%22%3E%3C/script%3E'));
                </script>
                <script>
                    var chart;
                    var graph;

                    var chartData = {9};

                    AmCharts.ready(function () {{
                        // SERIAL CHART
                        chart = new AmCharts.AmSerialChart();

                        chart.dataProvider = chartData;
                        chart.marginLeft = 10;
                        chart.categoryField = "match";

                        // AXES
                        // category
                        var categoryAxis = chart.categoryAxis;
                        categoryAxis.dashLength = 3;
                        categoryAxis.minorGridEnabled = true;
                        categoryAxis.minorGridAlpha = 0.1;

                        // value
                        var valueAxis = new AmCharts.ValueAxis();
                        valueAxis.position = "left";
                        valueAxis.axisColor = "#111111";
                        valueAxis.gridAlpha = 0;
                        valueAxis.axisThickness = 2;
                        chart.addValueAxis(valueAxis)

                        var valueAxis2 = new AmCharts.ValueAxis();
                        valueAxis2.position = "right";
                        valueAxis2.axisColor = "#FCD202";
                        valueAxis2.gridAlpha = 0;
                        valueAxis2.axisThickness = 2;
                        chart.addValueAxis(valueAxis2);

                        // GRAPH
                        graph = new AmCharts.AmGraph();
                        graph.title = "Auto Switch";
                        graph.valueAxis = valueAxis;
                        graph.type = "smoothedLine"; // this line makes the graph smoothed line.
                        graph.lineColor = "#637bb6";
                        graph.bullet = "round";
                        graph.bulletSize = 8;
                        graph.bulletBorderColor = "#FFFFFF";
                        graph.bulletBorderAlpha = 1;
                        graph.bulletBorderThickness = 2;
                        graph.lineThickness = 2;
                        graph.valueField = "autoswitch";
                        graph.balloonText = "Auto Switch:<br><b><span style='font-size:14px;'>[[value]]</span></b>";
                        chart.addGraph(graph);

                        graph2 = new AmCharts.AmGraph();
                        graph2.title = "Auto Scale";
                        graph2.valueAxis = valueAxis2;
                        graph2.type = "smoothedLine"; // this line makes the graph smoothed line.
                        graph2.lineColor = "#187a2e";
                        graph2.bullet = "round";
                        graph2.bulletSize = 8;
                        graph2.bulletBorderColor = "#FFFFFF";
                        graph2.bulletBorderAlpha = 1;
                        graph2.bulletBorderThickness = 2;
                        graph2.lineThickness = 2;
                        graph2.valueField = "autoscale";
                        graph2.balloonText = "Auto Scale:<br><b><span style='font-size:14px;'>[[value]]</span></b>";
                        chart.addGraph(graph2);

                        graph3 = new AmCharts.AmGraph();
                        graph3.title = "Tele Switch";
                        graph3.valueAxis = valueAxis;
                        graph3.type = "smoothedLine"; // this line makes the graph smoothed line.
                        graph3.lineColor = "#FF6600";
                        graph3.bullet = "round";
                        graph3.bulletSize = 8;
                        graph3.bulletBorderColor = "#FFFFFF";
                        graph3.bulletBorderAlpha = 1;
                        graph3.bulletBorderThickness = 2;
                        graph3.lineThickness = 2;
                        graph3.valueField = "teleswitch";
                        graph3.balloonText = "Tele Switch:<br><b><span style='font-size:14px;'>[[value]]</span></b>";
                        chart.addGraph(graph3);

                        graph4 = new AmCharts.AmGraph();
                        graph4.valueAxis = valueAxis2;
                        graph4.title = "Tele Exchange";
                        graph4.type = "smoothedLine"; // this line makes the graph smoothed line.
                        graph4.lineColor = "#FCD202";
                        graph4.bullet = "round";
                        graph4.bulletSize = 8;
                        graph4.bulletBorderColor = "#FFFFFF";
                        graph4.bulletBorderAlpha = 1;
                        graph4.bulletBorderThickness = 2;
                        graph4.lineThickness = 2;
                        graph4.valueField = "teleexch";
                        graph4.balloonText = "Tele Exchange:<br><b><span style='font-size:14px;'>[[value]]</span></b>";
                        chart.addGraph(graph4);

                        graph5 = new AmCharts.AmGraph();
                        graph5.valueAxis = valueAxis2;
                        graph5.title = "Dropped Gears";
                        graph5.type = "smoothedLine"; // this line makes the graph smoothed line.
                        graph5.lineColor = "#FF0000";
                        graph5.bullet = "round";
                        graph5.bulletSize = 8;
                        graph5.bulletBorderColor = "#FFFFFF";
                        graph5.bulletBorderAlpha = 1;
                        graph5.bulletBorderThickness = 2;
                        graph5.lineThickness = 2;
                        graph5.valueField = "cubedrop";
                        graph5.balloonText = "Dropped Cubes:<br><b><span style='font-size:14px;'>[[value]]</span></b>";
                        chart.addGraph(graph5);
                        
                        graph6 = new AmCharts.AmGraph();
                        graph6.valueAxis = valueAxis2;
                        graph6.title = "Tele Scale";
                        graph6.type = "smoothedLine"; // this line makes the graph smoothed line.
                        graph6.lineColor = "#FF2200";
                        graph6.bullet = "round";
                        graph6.bulletSize = 8;
                        graph6.bulletBorderColor = "#FFFFFF";
                        graph6.bulletBorderAlpha = 1;
                        graph6.bulletBorderThickness = 2;
                        graph6.lineThickness = 2;
                        graph6.valueField = "telescale";
                        graph6.balloonText = "Tele Scale:<br><b><span style='font-size:14px;'>[[value]]</span></b>";
                        chart.addGraph(graph6);

                        // CURSOR
                        var chartCursor = new AmCharts.ChartCursor();
                        chartCursor.cursorAlpha = 0;
                        chartCursor.cursorPosition = "mouse";
                        chart.addChartCursor(chartCursor);

                        var legend = new AmCharts.AmLegend();
                        legend.marginLeft = 110;
                        legend.useGraphSettings = true;
                        chart.addLegend(legend);
                        chart.creditsPosition = "bottom-right";

                        // WRITE
                        chart.write("chartdiv");
                    }});

                    function flag(m, f)
                    {{
                        $.post(
                            "flag",
                            {{num: {0}, match: m, flagval: f}}
                        );
                        window.location.reload(true);
                    }}
                </script>
            </head>
            <body>
                <h1 class="big">Team {0}</h1>
                <h2><a style="color: #B20000" href='/'>PiScout Database</a></h2>
                <br><br>
                <div style="text-align:center;">
                    <div id="apr">
                        <p class="statbox" style="font-weight:bold; font-size:100%">Average Total:</p>
                        <p style="font-size: 400%; line-height: 0em">{2}</p>
                    </div>
                    <div id="stats">
                        <p class="statbox" style="font-weight:bold">Average Match:</p>
                        <p class="statbox">Auto Switch: {3}</p>
                        <p class="statbox">Auto Scale: {4}</p>
                        <p class="statbox">Tele Switch: {5}</p>
                        <p class="statbox">Tele Scale: {6}</p>
                        <p class="statbox">Tele Exchange: {7}</p>
                        <p class="statbox">Endgame Points: {8}</p>
                    </div>
                </div>
                <br>
                <div id="chartdiv" style="width:1000px; height:400px; margin: 0 auto;"></div>
                <br>
                <table>
                    <thead><tr>
                        <th>Match</th>
                        <th>Auto</th>
                        <th>Teleop</th>
                        <th>Endgame</th>
                        <th>Other</th>
                        <th>Comments</th>
                        <th>Flag</th>
                    </tr></thead>{1}
                </table>
                {10}
                <br>
                <br>
                <p style="text-align: center; font-size: 24px"><a href="/matches?n={0}">View this team's match schedule</a></p>
            </body>
        </html>'''.format(n, output, s[2], s[3], s[4], s[5], s[6], s[7], s[8], str(dataset).replace("'", '"'),imcode,commentstr)

        # Called to flag a data entry

    @cherrypy.expose()
    def compare(self, t='team'):
        return '''
            <html>
                <head>
                    <title>PiScout</title>
                    <link href="http://fonts.googleapis.com/css?family=Chau+Philomene+One" rel="stylesheet" type="text/css">
                    <link href="/static/css/style.css" rel="stylesheet">
                </head>
                <body>
                    <h1 class="big">Compare {0}s</h1>
                    <h2><a style="color: #B20000" href='/'>PiScout Database</a></h2>
                    <br><br>
                    {1}
            </html>'''.format(t.capitalize(), '''
                    <p class="main">Enter up to 4 teams</p>
                    <form method="get" action="teams">
                        <input class="field" type="text" maxlength="4" name="n1" autocomplete="off"/>
                        <input class="field" type="text" maxlength="4" name="n2" autocomplete="off"/>
                        <input class="field" type="text" maxlength="4" name="n3" autocomplete="off"/>
                        <input class="field" type="text" maxlength="4" name="n4" autocomplete="off"/>
                        <button class="submit" type="submit">Submit</button>
                    </form>
            ''' if t == 'team' else '''
                    <p class="main">Enter two alliances</p>
                    <form method="get" action="alliances" style="text-align: center; width: 800px; margin: 0 auto;">
                        <div style="display: table;">
                            <div style="display:table-cell;">
                                <input class="field" type="text" maxlength="4" name="b1" autocomplete="off"/>
                                <input class="field" type="text" maxlength="4" name="b2" autocomplete="off"/>
                                <input class="field" type="text" maxlength="4" name="b3" autocomplete="off"/>
                            </div>
                            <div style="display:table-cell;">
                                <p style="font-size: 64px; line-height: 2.4em;">vs</p>
                            </div>
                            <div style="display:table-cell;">
                                <input class="field" type="text" maxlength="4" name="r1" autocomplete="off"/>
                                <input class="field" type="text" maxlength="4" name="r2" autocomplete="off"/>
                                <input class="field" type="text" maxlength="4" name="r3" autocomplete="off"/>
                            </div>
                        </div>
                        <button class="submit" type="submit">Submit</button>
                    </form>''')
    @cherrypy.expose()
    def flag(self, num='', match='', flagval=0):
        if not (num.isdigit() and match.isdigit()):
            return '<img src="http://goo.gl/eAs7JZ" style="width: 1200px"></img>'
        conn = sql.connect(self.datapath())
        cursor = conn.cursor()
        cursor.execute('UPDATE scout SET flag=? WHERE d0=? AND d1=?', (int(not int(flagval)), num, match))
        conn.commit()
        conn.close()
        self.calcavg(num)
        return ''

    # Input interface to compare teams or alliances
    # This probably won't ever need to be modified
    @cherrypy.expose()
    def compare(self, t='team'):
        return '''
            <html>
                <head>
                    <title>PiScout</title>
                    <link href="https://fonts.googleapis.com/css?family=Oxygen" rel="stylesheet" type="text/css">
                    <link href="/static/css/style.css" rel="stylesheet">
                </head>
                <body>
                    <h1 class="big">Compare {0}s</h1>
                    <h2><a style="color: #B20000" href='/'>PiScout Database</a></h2>
                    <br><br>
                    {1}
            </html>'''.format(t.capitalize(), '''
                    <p class="main">Enter up to 4 teams</p>
                    <form method="get" action="teams">
                        <input class="field" type="text" maxlength="4" name="n1" autocomplete="off"/>
                        <input class="field" type="text" maxlength="4" name="n2" autocomplete="off"/>
                        <input class="field" type="text" maxlength="4" name="n3" autocomplete="off"/>
                        <input class="field" type="text" maxlength="4" name="n4" autocomplete="off"/>
                        <button class="submit" type="submit">Submit</button>
                    </form>
            ''' if t == 'team' else '''
                    <p class="main">Enter two alliances</p>
                    <form method="get" action="alliances" style="text-align: center; width: 800px; margin: 0 auto;">
                        <div style="display: table;">
                            <div style="display:table-cell;">
                                <input class="field" type="text" maxlength="4" name="b1" autocomplete="off"/>
                                <input class="field" type="text" maxlength="4" name="b2" autocomplete="off"/>
                                <input class="field" type="text" maxlength="4" name="b3" autocomplete="off"/>
                            </div>
                            <div style="display:table-cell;">
                                <p style="font-size: 64px; line-height: 2.4em;">vs</p>
                            </div>
                            <div style="display:table-cell;">
                                <input class="field" type="text" maxlength="4" name="r1" autocomplete="off"/>
                                <input class="field" type="text" maxlength="4" name="r2" autocomplete="off"/>
                                <input class="field" type="text" maxlength="4" name="r3" autocomplete="off"/>
                            </div>
                        </div>
                        <button class="submit" type="submit">Submit</button>
                    </form>''')

    # Output for team comparison
    @cherrypy.expose()
    def teams(self, n1='', n2='', n3='', n4=''):
        nums = [n1, n2, n3, n4]
        averages = []
        conn = sql.connect(self.datapath())
        cursor = conn.cursor()
        output = ''
        for n in nums:
            if not n:
                continue
            if not n.isdigit():
                raise cherrypy.HTTPError(400, "You fool! Enter NUMBERS, not letters.")
            average = cursor.execute('SELECT * FROM averages WHERE team=?', (n,)).fetchall()
            assert len(average) < 2
            if len(average):
                entry = average[0]
            else:
                entry = [0] * 7
            # Add a data entry for each team
            output += '''<div style="text-align:center; display: inline-block; margin: 16px;">
                                <p><a href="/team?n={0}" style="font-size: 32px; line-height: 0em;">Team {0}</a></p>
                                <div id="apr">
                                    <p style="font-size: 100%; margin: 0.65em; line-height: 0.1em">Average Cubes</p>
                                    <p style="font-size: 400%; line-height: 0em">{7}</p>
                                </div>
                                <div id="stats">
                                    <p class="statbox" style="font-weight:bold">Match Averages:</p>
                                    <p class="statbox">Auto Switch: {1}</p>
                                    <p class="statbox">Auto Scale: {2}</p>
                                    <p class="statbox">Tele Switch: {3}</p>
                                    <p class="statbox">Tele Scale: {4}</p>
                                    <p class="statbox">Tele Exch: {5}</p>
                                    <p class="statbox">Endgame: {6}</p>
                                </div>
                            </div>'''.format(n, entry[3], entry[4],entry[5], entry[6],entry[7],entry[8],round(entry[2],1))  # unpack the elements
        conn.close()

        return '''
            <html>
                <head>
                    <title>PiScout</title>
                    <link href="https://fonts.googleapis.com/css?family=Oxygen" rel="stylesheet" type="text/css">
                    <link href="/static/css/style.css" rel="stylesheet">
                </head>
                <body>
                    <h1 class="big">Compare Teams</h1>
                    <h2><a style="color: #B20000" href='/'>PiScout Database</a></h2>
                    <br><br>
                    <div style="margin: 0 auto; text-align: center; max-width: 900px;">
                    {0}
                    <br><br><br>
                    </div>
                </body>
            </html>'''.format(output)

    # Output for alliance comparison
    @cherrypy.expose()
    def alliances(self, b1='', b2='', b3='', r1='', r2='', r3=''):
        nums = [b1, b2, b3, r1, r2, r3]
        averages = []
        conn = sql.connect(self.datapath())
        cursor = conn.cursor()
        # start a div table for the comparison
        # to later be formatted with sum APR
        apr = []
        output = ''
        # iterate through all six teams
        for i, n in enumerate(nums):
            # at halfway pointm switch to the second row
            if not n.isdigit():
                raise cherrypy.HTTPError(400, "You fool! Enter six valid team numbers!")
            average = cursor.execute('SELECT * FROM averages WHERE team=?', (n,)).fetchall()
            assert len(average) < 2
            if len(average):
                entry = average[0]
            else:
                entry = [0] * 7
            apr.append(entry[1])
            output += '''<div style="text-align:center; display: inline-block; margin: 16px;">
                                <p><a href="/team?n={0}" style="font-size: 32px; line-height: 0em;">Team {0}</a></p>
                                <div id="apr">
                                    <p style="font-size: 100%; margin: 0.65em; line-height: 0.1em">Average Cubes</p>
                                    <p style="font-size: 400%; line-height: 0em">{7}</p>
                                </div>
                                <div id="stats">
                                    <p class="statbox" style="font-weight:bold">Match Averages:</p>
                                    <p class="statbox">Auto Switch: {1}</p>
                                    <p class="statbox">Auto Scale: {2}</p>
                                    <p class="statbox">Tele Switch: {3}</p>
                                    <p class="statbox">Tele Scale: {4}</p>
                                    <p class="statbox">Tele Exch: {5}</p>
                                    <p class="statbox">Endgame: {6}</p>
                                </div>
                            </div>'''.format(n, entry[3], entry[4],entry[5], entry[6],entry[7],entry[8],round(entry[2],1))  # unpack the elements
        output += "</div></div>"
        prob_red = 1 / (
            1 + math.e ** (-0.08099 * (sum(apr[3:6]) - sum(apr[0:3]))))  # calculates win probability from 2016 data
        output = output.format(sum(apr[0:3]), sum(apr[3:6]), round((1 - prob_red) * 100, 1), round(prob_red * 100, 1))
        output = output.format()
        conn.close()

        return '''
            <html>
                <head>
                    <title>PiScout</title>
                    <link href="https://fonts.googleapis.com/css?family=Oxygen" rel="stylesheet" type="text/css">
                    <link href="/static/css/style.css" rel="stylesheet">
                </head>
                <body>
                    <h1 class="big">Compare Alliances</h1>
                    <h2><a style="color: #B20000" href='/'>PiScout Database</a></h2>
                    <br><br>
                    <div style="margin: 0 auto; text-align: center; max-width: 1000px;">
                    {0}
                    <br><br><br>
                    </div>
                </body>
            </html>'''.format(output)

        # Lists schedule data from TBA
    @cherrypy.expose()
    def matches(self, n=0):
        n = int(n)
        event = self.getevent()
        datapath = 'data_' + event + '.db'
        self.database_exists(event)
        conn = sql.connect(datapath)
        cursor = conn.cursor()
        m = []

        headers = {"X-TBA-App-Id": "frc2067:scouting-system:v01"}
        try:
            if n:
                # request a specific team
                m = requests.get("http://www.thebluealliance.com/api/v2/team/frc{0}/event/{1}/matches".format(n, event),
                                 params=headers)
            else:
                # get all the matches from this event
                m = requests.get("http://www.thebluealliance.com/api/v2/event/{0}/matches".format(event),
                                 params=headers)
            if m.status_code == 400:
                raise cherrypy.HTTPError(400, "Request rejected by The Blue Alliance.")
            with open(event + "_matches.json", "w+") as file:
                file.write(str(m.text))
            m = m.json()
        except:
            try:
                with open(event + '_matches.json') as matches_data:
                    m = json.load(matches_data)
            except:
                m = []

        output = ''

        if 'feed' in m:
            raise cherrypy.HTTPError(503, "Unable to retrieve data about this event.")

        # assign weights, so we can sort the matches
        for match in m:
            match['value'] = match['match_number']
            type = match['comp_level']
            if type == 'qf':
                match['value'] += 1000
            elif type == 'sf':
                match['value'] += 2000
            elif type == 'f':
                match['value'] += 3000

        m = sorted(m, key=lambda k: k['value'])
        for match in m:
            if match['comp_level'] != 'qm':
                match['num'] = match['comp_level'].upper() + ' ' + str(match['match_number'])
            else:
                match['num'] = match['match_number']
            output += '''
                <tr>
                    <td><a href="alliances?b1={1}&b2={2}&b3={3}&r1={4}&r2={5}&r3={6}">{0}</a></td>
                    <td><a href="team?n={1}">{1}</a></td>
                    <td><a href="team?n={2}">{2}</a></td>
                    <td><a href="team?n={3}">{3}</a></td>
                    <td><a href="team?n={4}">{4}</a></td>
                    <td><a href="team?n={5}">{5}</a></td>
                    <td><a href="team?n={6}">{6}</a></td>
                    <td>{7}</td>
                    <td>{8}</td>
                </tr>
                '''.format(match['num'], match['alliances']['blue']['teams'][0][3:],
                           match['alliances']['blue']['teams'][1][3:], match['alliances']['blue']['teams'][2][3:],
                           match['alliances']['red']['teams'][0][3:], match['alliances']['red']['teams'][1][3:],
                           match['alliances']['red']['teams'][2][3:], match['alliances']['blue']['score'],
                           match['alliances']['red']['score'])

        return '''
                <html>
                <head>
                    <title>PiScout</title>
                    <link href="https://fonts.googleapis.com/css?family=Oxygen" rel="stylesheet" type="text/css">
                    <link href="/static/css/style.css" rel="stylesheet">
                </head>
                <body>
                    <h1>Matches{0}</h1>
                    <h2><a style="color: #B20000" href='/'>PiScout Database</a></h2>
                    <br><br>
                    <table>
                    <thead><tr>
                        <th>Match</th>
                        <th>Blue 1</th>
                        <th>Blue 2</th>
                        <th>Blue 3</th>
                        <th>Red 1</th>
                        <th>Red 2</th>
                        <th>Red 3</th>
                        <th>Blue Score</th>
                        <th>Red Score</th>
                    </tr></thead>
                    <tbody>
                    {1}
                    </tbody>
                    </table>
                </body>
                </html>
            '''.format(": {}".format(n) if n else "", output)

        # Used by the scanning program to submit data, and used by comment system to submit data
        # this won't ever need to change
    @cherrypy.expose()
    def submit(self, data='', event='', team='', comment=''):
        if not (data or team):
            return '''
                    <h1>FATAL ERROR</h1>
                    <h3>DATA CORRUPTION</h3>
                    <p>Erasing database to prevent further damage to the system.</p>'''

        if data == 'json':
            return '[]'  # bogus json for local version

        datapath = 'data_' + event + '.db'
        self.database_exists(event)
        conn = sql.connect(datapath)
        cursor = conn.cursor()

        d = literal_eval(data)

        if team:
            if not comment:
                conn.close()
                raise cherrypy.HTTPRedirect('/team?n=' + str(team))
            cursor.execute('INSERT INTO comments VALUES (?, ?)', (team, d[17]))
            conn.commit()
            conn.close()
            raise cherrypy.HTTPRedirect('/team?n=' + str(team))
        d.append('0')
        y = ','.join(d)
        cursor.execute('INSERT INTO scout VALUES (' + y + ')')
        #[str(a) for a in d]
        conn.commit()
        conn.close()

        self.calcavg(d[0], event)
        self.calcmaxes(d[0], event)
        return ''


    def calcavg(self, n, event):
        datapath = 'data_' + event + '.db'
        conn = sql.connect(datapath)
        cursor = conn.cursor()
        #delete the existing entry, if a team has no matches they will be removed
        cursor.execute('DELETE FROM averages WHERE team=?',(n,))
        #d0 is the identifier for team, d1 is the identifier for match
        entries = cursor.execute('SELECT * FROM scout WHERE d0=? AND flag=0 ORDER BY d1 DESC', (n,)).fetchall()
        s = {'total':0,'autoswitch': 0, 'autoscale': 0, 'teleswitch': 0, 'telescale': 0, 'teleexch':0, 'end': 0, 'defense': 0}
        apr = 0
        # Iterate through all entries (if any exist) and sum all categories (added one to all the entries here
        if entries:
            for e in entries:
                s['total'] += e[2] + e[3] + e[8] + e[7] + e[11] + e[9]
                apr += e[2] + 2*e[3] + 2*e[8] + e[7] + e[11] + 1.5*e[9]
                s['autoswitch'] += e[2]
                s['autoscale'] += e[3]
                s['teleswitch'] += (e[7] + e[11])/2
                s['telescale'] += e[8]
                s['teleexch'] += e[9]
                if e[12] or e[14]:
                    s['end'] += 30
                elif e[13]:
                    s['end'] += 5
                s['defense'] += e[15]

            # take the average (divide by number of entries)
            for key,val in s.items():
                s[key] = round(val/len(entries), 2)

            # formula for calculating APR (point contribution)
            #apr = s['autoballs'] + s['teleopballs'] + s['end']
            #if s['autogears']:
            #     apr += 20 * min(s['autogears'], 1)
            # if s['autogears'] > 1:
            #     apr += (s['autogears'] - 1) * 10
            #
            # apr += max(min(s['teleopgears'], 2 - s['autogears']) * 20, 0)
            # if s['autogears'] + s['teleopgears'] > 2:
            #     apr += min(s['teleopgears'] + s['autogears'] - 2, 4) * 10
            # if s['autogears'] + s['teleopgears'] > 6:
            #     apr += min(s['teleopgears'] + s['autogears'] - 6, 6) * 7
            # apr = int(apr)

            #replace the data entry with a new one
            cursor.execute('INSERT INTO averages VALUES (?,?,?,?,?,?,?,?,?)',(n,  apr, s['total'], s['autoswitch'], s['autoscale'], s['teleswitch'], s['telescale'], s['teleexch'], s['end']))
        conn.commit()
        conn.close()

    def calcmaxes(self, n, event):
        datapath = 'data_' + event + '.db'
        conn = sql.connect(datapath)
        cursor = conn.cursor()

        entries = cursor.execute('SELECT * FROM scout WHERE d0 = ? AND flag=0 ORDER BY d1 DESC', (n,)).fetchall()
        s = {'total': 0,  'autoswitch': 0, 'autoscale': 0, 'teleswitch': 0, 'telescale': 0, 'teleexch': 0, 'end': 0, 'defense': 0}
        apr = 0
        # Iterate through all entries (if any exist) and sum all categories
        if entries:
            for e in entries:
                s['total'] = max(s['total'], e[2] + e[3] + e[8] + e[7] + e[11] + e[9])
                apr += max(apr,e[2] + 2*e[3] + 2*e[8] + e[7] + e[11] + 1.5*e[9])
                s['autoswitch'] = max(s['autoswitch'], e[2])
                s['autoscale'] = max(s['autoscale'], e[3])
                s['teleswitch'] = max(s['teleswitch'], e[7] + e[11])
                s['telescale'] = max(s['telescale'], e[8])
                s['teleexch'] = max(s['teleexch'], e[9])
                s['end'] = max(s['end'], e[12])
                s['defense'] = max(s['defense'], e[15])
        for key, val in s.items():
            s[key] = round(val, 2)
        # replace the data entry with a new one
            cursor.execute('DELETE FROM maxes WHERE team=?', (n,))
            cursor.execute('INSERT INTO maxes VALUES (?,?,?,?,?,?,?,?,?)', (
                n, apr, s['total'],s['autoswitch'], s['autoscale'], s['teleswitch'], s['telescale'], s['teleexch'], s['end']))
        conn.commit()
        conn.close()

# Return the path to the database for this event
    def datapath(self):
        return 'data_' + self.getevent() + '.db'

# Return the selected event
    def getevent(self):
        if 'event' not in cherrypy.session:
            cherrypy.session['event'] = CURRENT_EVENT
        return cherrypy.session['event']

# Wrapper for requests, ensuring nothing goes terribly wrong
# This code is trash; it just works to avoid errors when running without internet
    def get(self, req, params=""):
        a = None
        try:
            a = requests.get(req, params=params)
            if a.status_code == 404:
                raise Exception  # freaking stupid laziness
        except:
            # stupid lazy solution for local mode
            a = requests.get('http://127.0.0.1:8000/submit?data=json')
        return a

    def database_exists(self, event):
        datapath = 'data_' + event + '.db'
        if not os.path.isfile(datapath):
            # Generate a new database with the three tables
            conn = sql.connect(datapath)
            cursor = conn.cursor()
            # Replace 36 with the number of entries in main.py
            cursor.execute('CREATE TABLE scout (' + ','.join(
                [('d' + str(a) + ' integer') for a in range(18)]) + ',flag integer' + ')')
            cursor.execute(
                '''CREATE TABLE averages (team integer, apr integer,total real,autosw real,autosc real, telesw real, telesc real, teleexch real, end real)''')
            cursor.execute(
                '''CREATE TABLE maxes (team integer,apr integer,total real,autosw real,autosc real, telesw real, telesc real, teleexch real, end real)''')
            cursor.execute('''CREATE TABLE comments (team integer, comment text)''')
            conn.close()
            # END OF CLASS


# Execution starts here
datapath = 'data_' + CURRENT_EVENT + '.db'

if not os.path.isfile(datapath):
    # Generate a new database with the three tables
    conn = sql.connect(datapath)
    cursor = conn.cursor()
    # Replace 36 with the number of entries in main.py
    cursor.execute(
        'CREATE TABLE scout (' + ','.join([('d' + str(a) + ' integer') for a in range(18)]) + ',flag integer' + ')')
    cursor.execute(
        '''CREATE TABLE averages (team integer,apr integer,total real,autosw real,autosc real, telesw real, telesc real, teleexch real, end real)''')
    cursor.execute(
        '''CREATE TABLE maxes (team integer,apr integer,total real,autosw real,autosc real, telesw real, telesc real, teleexch real, end real)''')
    cursor.execute('''CREATE TABLE comments (team integer, comment text)''')
    cursor.execute(
        '''CREATE TABLE matches (match_number integer, comp_level text, red1 integer, red2 integer, red3 integer, blue1 integer, blue2 integer, blue3 integer, red_score integer, blue_score integer)''')
    conn.close()

conf = {
    '/': {
        'tools.sessions.on': True,
        'tools.staticdir.root': os.path.abspath(os.getcwd())
    },
    '/static': {
        'tools.staticdir.on': True,
        'tools.staticdir.dir': './public'
    },
    'global': {
        'server.socket_host': '127.0.0.1',
        'server.socket_port': 80
    }
}

# start method only to be used on the local version

'''

conf = {
         '/': {
                 'tools.sessions.on': True,
                 'tools.staticdir.root': os.path.abspath(os.getcwd())
         },
         '/static': {
                 'tools.staticdir.on': True,
                 'tools.staticdir.dir': './public'
         },
        'global': {
                'server.socket_host': '127.0.0.1',
                'server.socket_port': 80
        }
}

cherrypy.quickstart(ScoutServer(), '/', conf)
'''
def start():
    cherrypy.quickstart(ScoutServer(), '/', conf)


# the following is run on the real server

