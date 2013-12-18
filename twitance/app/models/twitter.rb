class Twitter < ActiveRecord::Base
  # attr_accessible :handle, :tweet
  field :name, type: String
end
