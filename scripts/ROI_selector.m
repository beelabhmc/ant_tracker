[file, path]=uiputfile('*.txt','Save ROI Labels', 'roi_labels.txt');
vname=@(x) inputname(1);
if isequal(file,0) || isequal(path,0)
   disp('User clicked Cancel.')
else
   disp(['User selected ',fullfile(path,file),...
         ' and then clicked Save.'])
writetable(ROI,fullfile(path,file),'Delimiter','\t');
end
