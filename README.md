## About

issues_linker is a small project designed to link issues from various projects between Redmine and Github.

This project was created using **PyCharm** 2019.1.3 (Community Edition)


## Requirements

```
Linux / Ubuntu >= 16.04

Redmine >= 3.4.11

redmine_webhook >= 0.0.4

python >= 3.5.2

Django >= 2.2.4

djangorestframework >= 3.10.2

Jinja2 >= 2.10.1

requests >= 2.22.0
```

## Installation

To Install issues_linker, clone this repository to local directory.

### Installation via Linux console:

Open the console and type:

```
$ cd <SOME_PATH>/

$ git clone https://github.com/AlexanderND/issues_linker
```

Just wait a bit for your system to download the data, and you're good to go!

### Installation via Github:

If you have trouble installing issues_linker via console, Github provides another option to clone repositories. Just click the **Clone or download** button, wait for the archive to download and then extract it into some local directory.


## Setup

### Install Redmine server:

Skip this step, if you already have a Redmine server.

In order to install Redmine server, you first need to install gems. If you are using Ubuntu, try this:

https://gorails.com/setup/ubuntu/16.04

Then, install the Redmine server:

https://www.redmine.org/projects/redmine/wiki/RedmineInstall

### Setup Redmine server:

issues_linker uses webhook plugin for Redmine. In order for issues_linker to work correctly, you need to install the plugin on your Redmine server. Skip this step, if your Redmine server already has the plugin installed.

In order to install the plugin on your Redmine server, just click the link and follow the simple installation steps:

https://github.com/suer/redmine_webhook

### Setup bots:

issues_linker uses bots toy link issues. In order for the project to work correctly, you need to set up bots on Github and Redmine. Skip this step, if you already have bots set up on Github and your Redmine server

After you're done setting up the bots, you need to open up <SOME_PATH>/issues_linker/issues_linker/server_config.json and override default BOT_ID_GH and BOT_ID_RM with ids of your bots in Github and Redmine.

Then, you will need to provide issues_linker with your bot's api_keys. Generate api_keys from their profiles and input them into <SOME_PATH>/issues_linker/api_keys/api_key_redmine.txt and <SOME_PATH>/issues_linker/api_keys/api_key_github.txt respectively.

### Setup labels:

While linking projects, issues_linker will automatically create default labels in Github's repository.

But you will have to create the labels in Redmine yourself and provide issues_linker with theirs ids. You will have to manually edit the **tracker_ids_rm**, **status_ids_rm** and **priority_ids_rm** in server_config.json

You should change the default values in the lists to your values.

```
[id_in_list] (default_id_in_redmine)  | label_name

tracker_ids_rm:
[0] (4)   | Tracker: task
[1] (5)   | Tracker: bug

status_ids_rm:
[0] (7)   | Status: new
[1] (8)   | Status: working
[2] (9)   | Status: feedback
[3] (10)  | Status: verification
[4] (11)  | Status: rejected
[5] (12)  | Status: closed

priority_ids_rm:
[0] (11)  | Priority: normal
[1] (10)  | Priority: low
[2] (12)  | Priority: urgent
```

### Setup issues_linker:

Go back to server_config.json and edit allowed_ips.

Add to the list your Redmine server's ip and any other ip, from witch you want to be able to access issues_linker server.

Then, edit the secret_gh.

In order to make your connection to Github the most secure, open up the terminal and type:

```
$ ruby -rsecurerandom -e 'puts SecureRandom.hex(20)'
```

The command should output a random string of 20 characters. Override the default value of secret_gh with it.

For more info on secret tokens look into **Setting your secret token** on https://developer.github.com/webhooks/securing/


## Linking projects

Please note that issues_linker will erase all labels on your issues and replace them with standard labels: **Priority: normal**, **Tracker: task** and **Status: new**.

Also, from Github you are only allowed to change issue's **Tracker**, issues_linker will automatically correct the labels if you try to change something else. 

### Give your bots necessary permitions on the projects:

On Redmine: open up your project and add your bot into **Members**.

In order to do that, go into **Settings->Members->New Member**, type yor bot's name into the field and click **Add**.

On Github: open up your project's repository and add your bot into **Collaborators**.

In order to do that, go into **Settings->Collaborators**, type yor bot's name into the field and click **Add Colaborator**.

Pleaso note that, unlike in Redmine, your bot needs to accept the invitation! Just log in from your bot's account, go into **https://github.com/<SOME_REPOSITORY>/invitations** and click **accept**.

### Add webhooks to the projects:

On Redmine:

go into your project's **Settings->WebHook**, type into the field **http://<SERVER_IP>:9000/payloads_from_redmine/** and click **Add**.

On Github:

Go into your project's **Settings->Webhooks** and click **Add webhook**.

Type into the **Payload URl** field **http://<SERVER_IP>:9000/payloads_from_github/**

Choose **Content-type** as **application/json**

Set **Secret** to the value of your secret_gh in server_config.json, which you've generated previously. 

Then, choose **Let me select individual events** and select **Issues** and **Issue comments**


### Link the projects together:

First, you have to actually run the server. In order to do that, type in console:

```
$ cd <SOME_PATH>/issues_linker

$ python3 manage.py runserver 0:9000
```

In order to link projects, you just have to open up in your browser **http://<SERVER_IP>:9000/linked_projects/**, input the urls to your projects and click **POST**.

url_rm exemple: http://localhost:3000/projects/issues_linker

url_gh example: https://github.com/AlexanderND/issues_linker

That's it! Now, just sit back and watch issues_linker do the magic!


## Known issues

1. issues_linker won't automatically re-synchronize any updates, witch were made while the issues_linker server was down.

2. issues_linker allows to change issue's tracker label from github, but if you change issues's tracker and try to change some other labels, it will post a notification about the change in Redmine multiple times.

Feel free to contact me if you encounter any other problems (via e-mail: aleksandr.nenakhov@redsolution.ru).


## Planned

1. Automate the **Add webhooks to the projects** step.

2. Change the logic of correcting labels in Github (process each label individually).

3. Add bot phrase on correcting labels in Github: "You can't change the <LABEL_NAME> label from Github! Please, stop trying."

4. Add projects re-sync function, when the server starts up (in case issues_linker server was down for a long time).

5. Improve the linking procedure (make a form, automize, etc...).

6. Improve the installation and setup procedures (it's a bit complex right now, might be confusing for inexperienced users).
