> Name: Sulaiman

> NIM: 10119049

> This readme is made as a prerequisite for joining DSC ITB Student Branch

## About this project

*Have trouble with deleting custom url from bit.ly?*

*Wanna get a reserved custom url before your to-custom url exist?*

> **This is [sulai.pw](http://sulai.pw)**

**Note**: 
* The site is temporarily **shut down** due to inactivity (and *GCP's expensive CloudSQL* :sob:)
* Demo video can be found **[here](https://www.youtube.com/watch?v=gR-pavYH4ko)**
* The webpages to this date hasn't been very responsive for mobile view, as the main container still too big (need x-scroll)

This is another url shortener, but with added capabilities. First released on 6th July 2020, for my CS50x final project. This website is hosted at
**[Google Cloud Platform](https://cloud.google.com)**, was built with [Flask](https://palletsprojects.com/p/flask/) (+ Jinja & Werkzeug), [MySQL](https://www.mysql.com/),
[Hashids](https://hashids.org/python/), and (of course) HTML5, CSS3, Bootstrap 4, Javascript.

## How to Use

Straight from [sulai.pw](https://sulai.pw), you can shorten your url without logging in. You are then redirected to show your
all shorten links. However, without logged in, you can only shorten up to 5 URLs. You can delete it and create again, but you
can't customize or reserve a link.

To login, go straight to the navigation bar and there it is. For now, I haven't think of using email verification, so
registering to it is really easy. After that, you will be redirected to dashboard and you can see there are "Create" and
"Reserve" menu. To customize an existing link, you can do that in dashboard, choose the "Action" column.

## Me about GCP

Truthfully I had no experience in web deploying when I made this. In CS50, I learned about basic programming (until data structure) using C, Python, and SQL all using IDE provided by CS50. On the last 2-3 weeks, I took the *web track* and learned HTML, CSS, Javascript, and Flask but only until the point of how to build web locally, in the IDE provided.
That being said, I was freaked out to see how wide-ranged the GCP features are.

New facts that I found in GCP: (some of these may sound silly :laughing:)
* Source files are uploaded from explorer in the editor window. (It takes some time before I can realize this lol)
* GCP doesn't know what language we use to deploy the web, so it needs an *app.yaml* file.
* To install Python libraries just for one project, a *venv* must be created in that project. The libraries can be installed manually or automatically using a *requirements.txt*.
* SQL has its own feature in GCP, namely CloudSQL (contrast with what I did in CS50 IDE, just create a *.db* file inside the explorer)
* After creating the CloudSQL instance, the protocol needs to be included into the *app.yaml*
* Latest version of CloudSQL bills you for usage of 24 hours per day even if your website have no visitor that day. And it cost more than Rp1.000.000 a month for the standard SQL instance.

And new difficulties I found in GCP:
* Can't understand the error reporting and how to debug :cry:
* Don't know how to "preview" the code result, so I deployed it everytime a bit of the code changed.
* I had quite a hard time configuring `pymysql` library to the CloudSQL (thanks to a helpful youtube tutorial).

Overall, GCP feels so new to me and let's see if more projects are to come!

## That's it, thanks! :blush:
