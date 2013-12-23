class Twitter < ActiveRecord::Base
	include Tire::Model::Search
	include Tire::Model::Callbacks
  	attr_accessible :handle, :tweet

  	mapping do 
  		indexes :handle,	:index => :not_analyzed
  		indexes :tweet, 	:analyzer => 'snowball'
  	end
  	
  	

	
end