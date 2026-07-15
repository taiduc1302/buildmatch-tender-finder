TENDER_FINDER - SIMPLE START GUIDE
==================================

This file is for a normal Windows user. You can open it in Notepad.


START THE PROGRAM
-----------------

Double-click:

   Launch_TENDER_FINDER_GUI.bat

The first launch automatically prepares the private Python environment. This
can take several minutes and needs internet access to install packages. Later
launches open the GUI directly.


FIRST SAFE CHECK
----------------

1. Click Validate keywords.
2. Click Run Self-Test.
3. Require Self-Test PASS with 0 failed checks.

Self-Test and Offline/Test Run do not contact public tender sites.


RUN OPTIONS
-----------

Offline/Test Run
- Uses packaged and local inputs only.
- Best for a safe first run and weekly checks before going live.

Live Run
- Contacts the enabled public sources in config\sources.csv.
- Does not log in, store portal passwords, or bypass CAPTCHA.
- BC Bid may ask you to complete a visible browser check.


EDIT KEYWORDS
-------------

Open config\keywords.xlsx, edit the Keywords sheet, save, and click Validate
keywords before running. Set active to N to disable a rule. Every run
recalculates all records from the current file. Check Keyword_Change_Audit for
old/new score, tier, and bucket changes. Manual Assigned To, Status, Notes,
and Weekly Review Log entries are preserved.


ADD OR CHANGE SOURCES
---------------------

Open the Source Checks tab. You can Add Source, Edit Source, Enable / Disable,
Validate Registry, Test Selected Offline, or Test Selected Live. New sources
start disabled. A live source test contacts only the selected public source
after you confirm it.


EMAIL ALERT FILES
-----------------

1. Open Email Alert Intake.
2. Click Create / Open Email Import Folder.
3. Copy approved .eml files into that folder.
4. Click Test Email Import.
5. If the counts look right, click Run With Email Alerts.

TENDER_FINDER does not move or delete your source email files.


RESULTS
-------

Use Open Workbook or Open Output Folder after a successful run. Outputs,
manifests, logs, settings, and history are stored under:

   C:\tenderfinder_out

Normal runs do not write runtime data into the program folder.


IF SOMETHING DOES NOT WORK
--------------------------

Run Self-Test again. You can also double-click verify_package.bat; it uses the
same offline Self-Test. A FAIL is honest: inspect the shown manifest/output
folder before relying on the workbook.
