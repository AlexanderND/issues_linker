## About

issues_linker is a small project designed to link issues from various projects between Redmine and Github.

This project was created using **PyCharm** 2019.1.3 (Community Edition)

## How to Install.

In order to Install issues_linker on your local machine, you just simply need to clone this repository into some directory.

#### Installation via Linux console:

Open the console and cd into some path:

$ cd <SOME_PATH>/

Then, type in console:

$ git clone https://github.com/AlexanderND/issues_linker

Just wait a bit for your system to download the data, and you're good to go!

#### Installation via Github:
Github provides a better option to clone repositories. Just click the "Clone or download" button, wait for the archive to download and then extract it into some directory.


## How to Setup.

#### Install Redmine server:

Skip this step, if you already have a Redmine server.

In order to installl Redmine server, you first need to install gems. If you are using Ubuntu, try this:

https://gorails.com/setup/ubuntu/16.04

Then, install the Redmine server:

https://www.redmine.org/projects/redmine/wiki/RedmineInstall

#### Setup Redmine server:

issues_linker uses webhook plugin for Redmine. In order for issues_linker to work correctly, you need to install the plugin on your Redmine server. Skip this step, if your Redmine server already has the plugin installed.

In order to install the plugin on your Redmine server, just click the link and follow the simple installation steps:

https://github.com/suer/redmine_webhook

#### Setup bots:

issues_linker uses bots toy link issues. In order for the project to work correctly, you need to set up bots on Github and Redmine. You can use the default bot on Github - [RedsolutionBot](https://github.com/RedsolutionBot "bleep-bloop"), we won't mind, but you will have to set up a bot on your Redmine server.

After you're done setting up the bots, you need to open up <SOME_PATH>/issues_linker/issues_linker/server_config.json and override default BOT_ID_GH and BOT_ID_RM with ids of your bots in Github and Redmine.

## How to link projects.

#### Give your bots necessary permitions on the projects:

On Redmine: open up your project and add your bot into "Members".

In order to do that, go into "Settings->Members->New Member", type yor bot's name into the field and click "Add".

On Github: open up your project's repository and add your bot into "Collaborators".

In order to do that, go into "Settings->Collaborators", type yor bot's name into the field and click "Add Colaborator".

Pleaso note that, unlike in Redmine, your bot needs to accept the invitation! Just log in from your bot's account, go into "https://github.com/<SOME_REPOSITORY>/invitations" and click "accept".

#### Add webhooks to the projects:

On Redmine:

go into your project's "Settings->WebHook", type into the field "http://<SERVER_IP>:9000/payloads_from_redmine/" and click "Add".

On Github you will need to add 2 webhooks:

1. Go into your project's "Settings->Webhooks" and click "Add webhook".

Type into the "Payload URl" field "http://<SERVER_IP>:9000/payloads_from_github/"

Choose "Content-type" as "application/json"

Then, choose "Let me select individual events" and select **only** "Issues"

2. Go into your project's "Settings->Webhooks" and click "Add webhook".

Type into the "Payload URl" field "http://<SERVER_IP>:9000/comment_payloads_from_github/"

Choose "Content-type" as "application/json"

Then, choose "Let me select individual events" and select **only** "Issue comments"

#### Link the projects together:

First, you have to actually run the server. In order to do that, just type in console:


$ cd ./PycharmProjects/issues_linker

$ python3 manage.py runserver 0:9000

In order to link projects, you just have to open up in your browser "http://<SERVER_IP>:9000/linked_projects/", input the urls to your projects and click "POST".

url_rm exemple: http://localhost:3000/projects/issues_linker

url_gh example: https://github.com/AlexanderND/issues_linker

That's it! Now, just sit back and watch issues_linker do the magic!

Note that the "Add webhooks to the projects" step *might* be automized in future releases.

Feel free to contact me if you encounter any problems (via e-mail: aleksandr.nenakhov@redsolution.ru).
