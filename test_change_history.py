from addict import Dict


def __a__b__c():
    pass


model = Dict({"x": 1}, track_changes=True)


model.metadata_report.delimiter = None
model.metadata_report.cols_type = None
model.vinput.csv_file_input = {'a': 5}
model.metadata_report.delimiter = ','
model.metadata_report.cols_type = [
    Dict({'n1': [1]}, track_changes=True), Dict({'n2': [3]}, track_changes=True)]


print("___change history_")
for _ in model.get_changed_history():
    print(_)

model.clear_changed_history()
