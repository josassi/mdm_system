# T0 Baseline Records Required for SCD2 Testing

The following records should exist in T0 (sources/ folder) for SCD2 test scenarios to work properly.

**IMPORTANT:** This is a REFERENCE file only. Do NOT overwrite existing sources/ data.
If these records don't exist, manually add them to the appropriate source CSV files.


## leads (8 records needed)

Required records (key fields only):

```csv
lead_id,first_name,last_name,email,phone
L009,Alice,Chen,alice.old@email.com,+852-9123-4567
L011,NullTest,Person,nulltest@email.com,
L012,RemoveAttr,Person,removeattr@email.com,+852-9122-2222
L016,FKTest,Person,fktest@email.com,+852-9155-5555
L301,MergeTarget,Person,merge.target@email.com,+852-9301-0001
L401,SplitSource,Person,split.source@email.com,+852-9401-0001
L024,Rapid,Changes,rapid.old@email.com,+852-9188-8888
L027,王小明,Unicode,unicode@email.com,+852-9211-1111
```

## quotes (4 records needed)

Required records (key fields only):

```csv
quote_id,lead_id,status
Q016,,Accepted
Q301,,Accepted
Q401,L401,Accepted
Q402,L401,Accepted
```

## quote_members (2 records needed)

Required records (key fields only):

```csv
qm_id,quote_id,member_sequence,first_name,last_name
QM301,Q301,1,MergeMember,One
QM302,Q301,2,MergeMember,Two
```

## policy_members (1 records needed)

Required records (key fields only):

```csv
pm_id,first_name,last_name,gov_id_number
PM013,Jonh,Corrected,C130000(0)
```
