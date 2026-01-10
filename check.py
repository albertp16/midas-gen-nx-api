data = {'empty': {'FORCE': 'KN', 'DIST': 'M', 'HEAD': 
           ['Index', 'Load Case', 'Story', 'Story Height', 'P-Delta Incremental Factor', 'Allowable Story Drift Ratio', 'Maximum Drift of All Vertical Elements/Node', 'Maximum Drift of All Vertical Elements/Story Drift', 'Maximum Drift of All Vertical Elements/Modified Drift', 'Maximum Drift of All Vertical Elements/Story Drift Ratio', 'Maximum Drift of All Vertical Elements/Remark', 'Drift at the Center of Mass/Story Drift', 'Drift at the Center of Mass/Modified Drift', 'Drift at the Center of Mass/Drift Factor', 'Drift at the Center of Mass/Story Drift Ratio', 'Drift at the Center of Mass/Remark'], 
           'DATA': [
               ['1', 'Ex +', '4F', '3.75', '1.00', '0.03', '138', '-0.00', '-0.00', '-0.00', 'OK', '-0.00', '-0.00', '8.77', '-0.00', 'OK'], 
               ['2', 'Ex +', '3F', '3.75', '1.00', '0.03', '95', '-0.00', '-0.00', '-0.00', 'OK', '-0.00', '-0.00', '13.46', '-0.00', 'OK'], 
               ['3', 'Ex +', '2F', '3.75', '1.00', '0.03', '16', '0.00', '0.00', '0.00', 'OK', '-0.00', '-0.00', '30.67', '-0.00', 'OK'], 
               ['4', 'Ex +', '1F', '3.75', '1.00', '0.03', '1', '-0.00', '-0.00', '-0.00', 'OK', '0.00', '0.00', '126.05', '0.00', 'OK']
               ]
               }
               }

print(data['empty']['DATA'])


output = {'empty': {'FORCE': 'KN', 'DIST': 'MM', 'HEAD': ['Index', 'Load Case', 'Story', 'Story Height', 'P-Delta Incremental Factor', 'Allowable Story Drift Ratio', 'Maximum Drift of All Vertical Elements/Node', 'Maximum Drift of All Vertical Elements/Story Drift', 'Maximum Drift of All Vertical Elements/Modified Drift', 'Maximum Drift of All Vertical Elements/Story Drift Ratio', 'Maximum Drift of All Vertical Elements/Remark', 'Drift at the Center of Mass/Story Drift', 'Drift at the Center of Mass/Modified Drift', 'Drift at the Center of Mass/Drift Factor', 'Drift at the Center of Mass/Story Drift Ratio', 'Drift at the Center of Mass/Remark'], 'DATA': [['1', 'Ex +', '4F', '3750.00000', '1.00000', '0.02500', '138', '-0.38175', '-2.27142', '-0.00061', 'OK', '-0.04352', '-0.25894', '8.77205', '-0.00007', 'OK'], ['2', 'Ex +', '3F', '3750.00000', '1.00000', '0.02500', '95', '-0.44066', '-2.62191', '-0.00070', 'OK', '-0.03273', '-0.19477', '13.46151', '-0.00005', 'OK'], ['3', 'Ex +', '2F', '3750.00000', '1.00000', '0.02500', '16', '0.26868', '1.59863', '0.00043', 'OK', '-0.00906', '-0.05389', '30.66659', '-0.00001', 'OK'], ['4', 'Ex +', '1F', '3750.00000', '1.00000', '0.02500', '1', '-0.24098', '-1.43382', '-0.00038', 'OK', '0.00193', '0.01147', '126.05337', '0.00000', 'OK']]}}