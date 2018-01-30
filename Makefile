# This Makefile requires an internal tool. Sorry.
PACKAGE = getconf

include $(shell makefile_path python.mk)

release:
	fullrelease
