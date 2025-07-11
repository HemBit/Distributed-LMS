# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# NO CHECKED-IN PROTOBUF GENCODE
# source: login.proto
# Protobuf Python Version: 5.27.2
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import runtime_version as _runtime_version
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
_runtime_version.ValidateProtobufRuntimeVersion(
    _runtime_version.Domain.PUBLIC,
    5,
    27,
    2,
    '',
    'login.proto'
)
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x0blogin.proto\x12\x03lms\"2\n\x0cLoginRequest\x12\x10\n\x08username\x18\x01 \x01(\t\x12\x10\n\x08password\x18\x02 \x01(\t\"B\n\rLoginResponse\x12\r\n\x05token\x18\x01 \x01(\t\x12\x0f\n\x07message\x18\x02 \x01(\t\x12\x11\n\tuser_type\x18\x03 \x01(\t\"A\n\x17\x41ssignmentUploadRequest\x12\r\n\x05token\x18\x01 \x01(\t\x12\x17\n\x0f\x61ssignment_data\x18\x02 \x01(\x0c\"+\n\x18\x41ssignmentUploadResponse\x12\x0f\n\x07message\x18\x01 \x01(\t\" \n\x0f\x46\x65\x65\x64\x62\x61\x63kRequest\x12\r\n\x05token\x18\x01 \x01(\t\"C\n\x10\x46\x65\x65\x64\x62\x61\x63kResponse\x12\x10\n\x08\x66\x65\x65\x64\x62\x61\x63k\x18\x01 \x01(\t\x12\x0e\n\x06graded\x18\x02 \x01(\x08\x12\r\n\x05grade\x18\x03 \x01(\t\"(\n\x17\x41ssignmentStatusRequest\x12\r\n\x05token\x18\x01 \x01(\t\",\n\x18\x41ssignmentStatusResponse\x12\x10\n\x08uploaded\x18\x01 \x01(\x08\"s\n\x16GradeAssignmentRequest\x12\r\n\x05token\x18\x01 \x01(\t\x12\x15\n\rassignment_id\x18\x02 \x01(\x05\x12\r\n\x05grade\x18\x03 \x01(\t\x12\x10\n\x08\x66\x65\x65\x64\x62\x61\x63k\x18\x04 \x01(\t\x12\x12\n\nstudent_id\x18\x05 \x01(\t\"/\n\x1eViewUngradedAssignmentsRequest\x12\r\n\x05token\x18\x01 \x01(\t\"J\n\nAssignment\x12\x15\n\rassignment_id\x18\x01 \x01(\x05\x12\x12\n\nstudent_id\x18\x02 \x01(\t\x12\x11\n\tfile_path\x18\x03 \x01(\t\"G\n\x1fViewUngradedAssignmentsResponse\x12$\n\x0b\x61ssignments\x18\x01 \x03(\x0b\x32\x0f.lms.Assignment\"*\n\x17GradeAssignmentResponse\x12\x0f\n\x07message\x18\x01 \x01(\t\";\n\x0cQueryRequest\x12\r\n\x05token\x18\x01 \x01(\t\x12\r\n\x05title\x18\x02 \x01(\t\x12\r\n\x05query\x18\x03 \x01(\t\" \n\rQueryResponse\x12\x0f\n\x07message\x18\x01 \x01(\t\"\'\n\x16\x43heckQueryReplyRequest\x12\r\n\x05token\x18\x01 \x01(\t\"(\n\x17\x43heckQueryReplyResponse\x12\r\n\x05reply\x18\x01 \x01(\t\"J\n\x05Query\x12\x10\n\x08query_id\x18\x01 \x01(\x05\x12\r\n\x05title\x18\x02 \x01(\t\x12\x0c\n\x04\x62ody\x18\x03 \x01(\t\x12\x12\n\nstudent_id\x18\x04 \x01(\t\"!\n\x10QueryViewRequest\x12\r\n\x05token\x18\x01 \x01(\t\"0\n\x11QueryViewResponse\x12\x1b\n\x07queries\x18\x01 \x03(\x0b\x32\n.lms.Query\"Y\n\x13ReplyToQueryRequest\x12\r\n\x05token\x18\x01 \x01(\t\x12\x10\n\x08query_id\x18\x02 \x01(\x05\x12\r\n\x05reply\x18\x03 \x01(\t\x12\x12\n\nstudent_id\x18\x04 \x01(\t\"\'\n\x14ReplyToQueryResponse\x12\x0f\n\x07message\x18\x01 \x01(\t\"R\n\x1b\x43ourseMaterialUploadRequest\x12\r\n\x05token\x18\x01 \x01(\t\x12\r\n\x05title\x18\x02 \x01(\t\x12\x15\n\rmaterial_data\x18\x03 \x01(\x0c\"/\n\x1c\x43ourseMaterialUploadResponse\x12\x0f\n\x07message\x18\x01 \x01(\t\"*\n\x19\x43ourseMaterialListRequest\x12\r\n\x05token\x18\x01 \x01(\t\",\n\x1a\x43ourseMaterialListResponse\x12\x0e\n\x06titles\x18\x01 \x03(\t\"=\n\x1d\x43ourseMaterialDownloadRequest\x12\r\n\x05token\x18\x01 \x01(\t\x12\r\n\x05title\x18\x02 \x01(\t\"B\n\x1e\x43ourseMaterialDownloadResponse\x12\x0f\n\x07\x63ontent\x18\x01 \x01(\x0c\x12\x0f\n\x07message\x18\x02 \x01(\t\"2\n\x0fQuestionRequest\x12\r\n\x05token\x18\x01 \x01(\t\x12\x10\n\x08question\x18\x02 \x01(\t\"0\n\rAnswerRequest\x12\r\n\x05token\x18\x01 \x01(\t\x12\x10\n\x08question\x18\x02 \x01(\t\"/\n\x0e\x41nswerResponse\x12\r\n\x05token\x18\x01 \x01(\t\x12\x0e\n\x06\x61nswer\x18\x02 \x01(\t\"7\n\x12RequestVoteRequest\x12\x0c\n\x04term\x18\x01 \x01(\x05\x12\x13\n\x0b\x63\x61ndidateId\x18\x02 \x01(\t\"6\n\x10RequestVoteReply\x12\x0c\n\x04term\x18\x01 \x01(\x05\x12\x14\n\x0cvote_granted\x18\x02 \x01(\x08\")\n\x08LogEntry\x12\x0c\n\x04term\x18\x01 \x01(\x05\x12\x0f\n\x07\x63ommand\x18\x02 \x01(\t\"\xae\x01\n\x14\x41ppendEntriesRequest\x12\x0c\n\x04term\x18\x01 \x01(\x05\x12\x10\n\x08leaderId\x18\x02 \x01(\t\x12\x15\n\rleaderAddress\x18\x03 \x01(\t\x12\x14\n\x0cprevLogIndex\x18\x04 \x01(\x05\x12\x13\n\x0bprevLogTerm\x18\x05 \x01(\x05\x12\x1e\n\x07\x65ntries\x18\x06 \x03(\x0b\x32\r.lms.LogEntry\x12\x14\n\x0cleaderCommit\x18\x07 \x01(\x05\"3\n\x12\x41ppendEntriesReply\x12\x0c\n\x04term\x18\x01 \x01(\x05\x12\x0f\n\x07success\x18\x02 \x01(\x08\"%\n\x14ValidateTokenRequest\x12\r\n\x05token\x18\x01 \x01(\t\"&\n\x15ValidateTokenResponse\x12\r\n\x05valid\x18\x01 \x01(\x08\x32\xa8\t\n\x03LMS\x12.\n\x05Login\x12\x11.lms.LoginRequest\x1a\x12.lms.LoginResponse\x12O\n\x10UploadAssignment\x12\x1c.lms.AssignmentUploadRequest\x1a\x1d.lms.AssignmentUploadResponse\x12<\n\rCheckFeedback\x12\x14.lms.FeedbackRequest\x1a\x15.lms.FeedbackResponse\x12T\n\x15\x43heckAssignmentStatus\x12\x1c.lms.AssignmentStatusRequest\x1a\x1d.lms.AssignmentStatusResponse\x12L\n\x0fGradeAssignment\x12\x1b.lms.GradeAssignmentRequest\x1a\x1c.lms.GradeAssignmentResponse\x12\x32\n\tPostQuery\x12\x11.lms.QueryRequest\x1a\x12.lms.QueryResponse\x12L\n\x0f\x43heckQueryReply\x12\x1b.lms.CheckQueryReplyRequest\x1a\x1c.lms.CheckQueryReplyResponse\x12<\n\x0bViewQueries\x12\x15.lms.QueryViewRequest\x1a\x16.lms.QueryViewResponse\x12\x43\n\x0cReplyToQuery\x12\x18.lms.ReplyToQueryRequest\x1a\x19.lms.ReplyToQueryResponse\x12[\n\x14UploadCourseMaterial\x12 .lms.CourseMaterialUploadRequest\x1a!.lms.CourseMaterialUploadResponse\x12V\n\x13ListCourseMaterials\x12\x1e.lms.CourseMaterialListRequest\x1a\x1f.lms.CourseMaterialListResponse\x12\x61\n\x16\x44ownloadCourseMaterial\x12\".lms.CourseMaterialDownloadRequest\x1a#.lms.CourseMaterialDownloadResponse\x12\x64\n\x17ViewUngradedAssignments\x12#.lms.ViewUngradedAssignmentsRequest\x1a$.lms.ViewUngradedAssignmentsResponse\x12\x46\n\rValidateToken\x12\x19.lms.ValidateTokenRequest\x1a\x1a.lms.ValidateTokenResponse\x12\x39\n\x0eGenerateAnswer\x12\x12.lms.AnswerRequest\x1a\x13.lms.AnswerResponse\x12\x38\n\x0b\x41skQuestion\x12\x14.lms.QuestionRequest\x1a\x13.lms.AnswerResponse2\x8a\x01\n\x04Raft\x12=\n\x0bRequestVote\x12\x17.lms.RequestVoteRequest\x1a\x15.lms.RequestVoteReply\x12\x43\n\rAppendEntries\x12\x19.lms.AppendEntriesRequest\x1a\x17.lms.AppendEntriesReplyb\x06proto3')

_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'login_pb2', _globals)
if not _descriptor._USE_C_DESCRIPTORS:
  DESCRIPTOR._loaded_options = None
  _globals['_LOGINREQUEST']._serialized_start=20
  _globals['_LOGINREQUEST']._serialized_end=70
  _globals['_LOGINRESPONSE']._serialized_start=72
  _globals['_LOGINRESPONSE']._serialized_end=138
  _globals['_ASSIGNMENTUPLOADREQUEST']._serialized_start=140
  _globals['_ASSIGNMENTUPLOADREQUEST']._serialized_end=205
  _globals['_ASSIGNMENTUPLOADRESPONSE']._serialized_start=207
  _globals['_ASSIGNMENTUPLOADRESPONSE']._serialized_end=250
  _globals['_FEEDBACKREQUEST']._serialized_start=252
  _globals['_FEEDBACKREQUEST']._serialized_end=284
  _globals['_FEEDBACKRESPONSE']._serialized_start=286
  _globals['_FEEDBACKRESPONSE']._serialized_end=353
  _globals['_ASSIGNMENTSTATUSREQUEST']._serialized_start=355
  _globals['_ASSIGNMENTSTATUSREQUEST']._serialized_end=395
  _globals['_ASSIGNMENTSTATUSRESPONSE']._serialized_start=397
  _globals['_ASSIGNMENTSTATUSRESPONSE']._serialized_end=441
  _globals['_GRADEASSIGNMENTREQUEST']._serialized_start=443
  _globals['_GRADEASSIGNMENTREQUEST']._serialized_end=558
  _globals['_VIEWUNGRADEDASSIGNMENTSREQUEST']._serialized_start=560
  _globals['_VIEWUNGRADEDASSIGNMENTSREQUEST']._serialized_end=607
  _globals['_ASSIGNMENT']._serialized_start=609
  _globals['_ASSIGNMENT']._serialized_end=683
  _globals['_VIEWUNGRADEDASSIGNMENTSRESPONSE']._serialized_start=685
  _globals['_VIEWUNGRADEDASSIGNMENTSRESPONSE']._serialized_end=756
  _globals['_GRADEASSIGNMENTRESPONSE']._serialized_start=758
  _globals['_GRADEASSIGNMENTRESPONSE']._serialized_end=800
  _globals['_QUERYREQUEST']._serialized_start=802
  _globals['_QUERYREQUEST']._serialized_end=861
  _globals['_QUERYRESPONSE']._serialized_start=863
  _globals['_QUERYRESPONSE']._serialized_end=895
  _globals['_CHECKQUERYREPLYREQUEST']._serialized_start=897
  _globals['_CHECKQUERYREPLYREQUEST']._serialized_end=936
  _globals['_CHECKQUERYREPLYRESPONSE']._serialized_start=938
  _globals['_CHECKQUERYREPLYRESPONSE']._serialized_end=978
  _globals['_QUERY']._serialized_start=980
  _globals['_QUERY']._serialized_end=1054
  _globals['_QUERYVIEWREQUEST']._serialized_start=1056
  _globals['_QUERYVIEWREQUEST']._serialized_end=1089
  _globals['_QUERYVIEWRESPONSE']._serialized_start=1091
  _globals['_QUERYVIEWRESPONSE']._serialized_end=1139
  _globals['_REPLYTOQUERYREQUEST']._serialized_start=1141
  _globals['_REPLYTOQUERYREQUEST']._serialized_end=1230
  _globals['_REPLYTOQUERYRESPONSE']._serialized_start=1232
  _globals['_REPLYTOQUERYRESPONSE']._serialized_end=1271
  _globals['_COURSEMATERIALUPLOADREQUEST']._serialized_start=1273
  _globals['_COURSEMATERIALUPLOADREQUEST']._serialized_end=1355
  _globals['_COURSEMATERIALUPLOADRESPONSE']._serialized_start=1357
  _globals['_COURSEMATERIALUPLOADRESPONSE']._serialized_end=1404
  _globals['_COURSEMATERIALLISTREQUEST']._serialized_start=1406
  _globals['_COURSEMATERIALLISTREQUEST']._serialized_end=1448
  _globals['_COURSEMATERIALLISTRESPONSE']._serialized_start=1450
  _globals['_COURSEMATERIALLISTRESPONSE']._serialized_end=1494
  _globals['_COURSEMATERIALDOWNLOADREQUEST']._serialized_start=1496
  _globals['_COURSEMATERIALDOWNLOADREQUEST']._serialized_end=1557
  _globals['_COURSEMATERIALDOWNLOADRESPONSE']._serialized_start=1559
  _globals['_COURSEMATERIALDOWNLOADRESPONSE']._serialized_end=1625
  _globals['_QUESTIONREQUEST']._serialized_start=1627
  _globals['_QUESTIONREQUEST']._serialized_end=1677
  _globals['_ANSWERREQUEST']._serialized_start=1679
  _globals['_ANSWERREQUEST']._serialized_end=1727
  _globals['_ANSWERRESPONSE']._serialized_start=1729
  _globals['_ANSWERRESPONSE']._serialized_end=1776
  _globals['_REQUESTVOTEREQUEST']._serialized_start=1778
  _globals['_REQUESTVOTEREQUEST']._serialized_end=1833
  _globals['_REQUESTVOTEREPLY']._serialized_start=1835
  _globals['_REQUESTVOTEREPLY']._serialized_end=1889
  _globals['_LOGENTRY']._serialized_start=1891
  _globals['_LOGENTRY']._serialized_end=1932
  _globals['_APPENDENTRIESREQUEST']._serialized_start=1935
  _globals['_APPENDENTRIESREQUEST']._serialized_end=2109
  _globals['_APPENDENTRIESREPLY']._serialized_start=2111
  _globals['_APPENDENTRIESREPLY']._serialized_end=2162
  _globals['_VALIDATETOKENREQUEST']._serialized_start=2164
  _globals['_VALIDATETOKENREQUEST']._serialized_end=2201
  _globals['_VALIDATETOKENRESPONSE']._serialized_start=2203
  _globals['_VALIDATETOKENRESPONSE']._serialized_end=2241
  _globals['_LMS']._serialized_start=2244
  _globals['_LMS']._serialized_end=3436
  _globals['_RAFT']._serialized_start=3439
  _globals['_RAFT']._serialized_end=3577
# @@protoc_insertion_point(module_scope)
