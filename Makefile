# This Makefile requires an internal tool. Sorry.
PACKAGE = getconf

include $(shell makefile-path python.mk)

release:
	fullrelease
